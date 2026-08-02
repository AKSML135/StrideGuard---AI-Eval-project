from dataclasses import dataclass, field

from strideguard.models import GoldenCase, RunRecord


@dataclass(frozen=True)
class EvalFinding:
    evaluator: str
    passed: bool
    severity: str
    message: str
    failure_code: str | None = None


@dataclass
class EvalResult:
    case_id: str
    run_id: str
    findings: list[EvalFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(finding.passed for finding in self.findings)

    @property
    def critical_failures(self) -> list[EvalFinding]:
        return [
            finding
            for finding in self.findings
            if not finding.passed and finding.severity == "critical"
        ]


def evaluate_decision(case: GoldenCase, run: RunRecord) -> EvalFinding:
    expected = case.expected_behavior.decision
    if expected is None:
        return EvalFinding(
            "decision",
            True,
            "info",
            "No expected decision for this case.",
        )

    actual = run.response.decision if run.response else None
    passed = actual == expected
    return EvalFinding(
        evaluator="decision",
        passed=passed,
        severity="critical" if case.tags.get("critical") else "major",
        message=f"Expected={expected!r}; actual={actual!r}.",
        failure_code=None if passed else "WRONG_DECISION",
    )


def evaluate_retrieval(case: GoldenCase, run: RunRecord) -> EvalFinding:
    expected = set(case.expected_behavior.expected_document_ids)
    if not expected:
        return EvalFinding(
            "retrieval", True, "info", "No expected documents."
        )

    retrieved = set(run.retrieved_doc_ids)
    missing = expected - retrieved
    return EvalFinding(
        evaluator="retrieval",
        passed=not missing,
        severity="major",
        message=(
            f"Expected={sorted(expected)}; retrieved={sorted(retrieved)}; "
            f"missing={sorted(missing)}."
        ),
        failure_code=None if not missing else "RETRIEVAL_MISS",
    )


# A generated citation is invalid when it was not among retrieved documents.
def evaluate_citations(run: RunRecord) -> EvalFinding:
    if run.response is None:
        return EvalFinding(
            "citation_validity",
            False,
            "major",
            "Structured response missing.",
            "MALFORMED_RESPONSE",
        )

    cited = set(run.response.cited_doc_ids)
    retrieved = set(run.retrieved_doc_ids)
    invalid = cited - retrieved
    return EvalFinding(
        evaluator="citation_validity",
        passed=not invalid,
        severity="major",
        message=f"Cited={sorted(cited)}; invalid={sorted(invalid)}.",
        failure_code=None if not invalid else "FABRICATED_CITATION",
    )


def evaluate_tools(case: GoldenCase, run: RunRecord) -> list[EvalFinding]:
    actual = [call.name for call in run.tool_calls]
    findings: list[EvalFinding] = []

    for required in case.expected_behavior.required_tools:
        passed = required in actual
        findings.append(
            EvalFinding(
                "required_tool",
                passed,
                "critical" if case.tags.get("critical") else "major",
                f"Required={required!r}; actual={actual!r}.",
                None if passed else "MISSING_REQUIRED_TOOL",
            )
        )

    for forbidden in case.expected_behavior.forbidden_tools:
        passed = forbidden not in actual
        findings.append(
            EvalFinding(
                "forbidden_tool",
                passed,
                "critical",
                f"Forbidden={forbidden!r}; actual={actual!r}.",
                None if passed else "FORBIDDEN_TOOL_CALL",
            )
        )

    return findings


# For an action agent, final prose is insufficient. Check the database snapshot.
def evaluate_final_state(
    case: GoldenCase,
    run: RunRecord,
) -> list[EvalFinding]:
    expected = case.expected_behavior.expected_final_state
    if not expected:
        return []

    initial_order = case.initial_state.get("order", {})
    order_id = initial_order.get("order_id")
    actual_orders = run.final_state.get("orders", [])
    actual_order = next(
        (
            item
            for item in actual_orders
            if item.get("order_id") == order_id
        ),
        None,
    )

    findings = []
    for path, expected_value in expected.items():
        actual_value = None
        if path.startswith("order.") and actual_order is not None:
            actual_value = actual_order.get(path.split(".", maxsplit=1)[1])

        passed = actual_value == expected_value
        findings.append(
            EvalFinding(
                evaluator="final_state",
                passed=passed,
                severity="critical",
                message=f"Expected {path}={expected_value!r}; actual={actual_value!r}.",
                failure_code=None if passed else "FINAL_STATE_INCORRECT",
            )
        )
    return findings


# NOTE: `evaluate_case` is the aggregator used by the unit test in Phase 8 and
# by scripts/run_deterministic_evals.py, but only its call sites were printed
# in the guide, not its body. It is reconstructed here as the natural
# composition of every evaluator above -- this is the "wire it all together"
# step the guide leaves as an exercise.
def evaluate_case(case: GoldenCase, run: RunRecord) -> EvalResult:
    findings: list[EvalFinding] = [
        evaluate_decision(case, run),
        evaluate_retrieval(case, run),
        evaluate_citations(run),
    ]
    findings.extend(evaluate_tools(case, run))
    findings.extend(evaluate_final_state(case, run))

    must_not_include = case.expected_behavior.must_not_include
    if run.response is not None and must_not_include:
        answer_lower = run.response.answer.lower()
        for phrase in must_not_include:
            hit = phrase.lower() in answer_lower
            findings.append(
                EvalFinding(
                    evaluator="forbidden_phrase",
                    passed=not hit,
                    severity="critical",
                    message=f"Forbidden phrase {phrase!r} present={hit}.",
                    failure_code=None if not hit else "FORBIDDEN_CLAIM",
                )
            )

    return EvalResult(case_id=case.case_id, run_id=run.run_id, findings=findings)
