"""Unit tests for the deterministic evaluators.

NOTE: the guide's Phase 8 text shows the `test_wrong_boundary_decision_is_critical`
test body verbatim but references three helpers (`CASES`, `make_run`,
`failure_codes`) without printing their implementations. They are
reconstructed below in the obvious way: `CASES` loads the golden dataset,
`make_run` builds a minimal frozen RunRecord for a given case, and
`failure_codes` flattens failure codes out of a list of EvalResult.
"""

from datetime import UTC, datetime
from pathlib import Path

from strideguard.datasets import load_cases
from strideguard.evaluators import EvalResult, evaluate_case
from strideguard.models import RunRecord, SupportAnswer, ToolCallRecord

DATASET = Path("evals/datasets/dev.jsonl")
CASES = {case.case_id: case for case in load_cases(DATASET)}


def make_run(
    *,
    case_id: str,
    decision: str,
    answer: str,
    retrieved: list[str] | None = None,
    cited: list[str] | None = None,
    tools: list[str] | None = None,
) -> RunRecord:
    return RunRecord(
        run_id=f"test-{case_id}",
        case_id=case_id,
        mode="baseline",
        provider="fake",
        model="fake-model",
        prompt_version="support-v1",
        knowledge_version="kb-v1",
        started_at=datetime.now(UTC),
        latency_ms=0.0,
        response=SupportAnswer(
            decision=decision,
            answer=answer,
            cited_doc_ids=cited or [],
        ),
        retrieved_doc_ids=retrieved or [],
        tool_calls=[ToolCallRecord(name=name) for name in (tools or [])],
    )


def failure_codes(results: list[EvalResult]) -> list[str]:
    return [
        finding.failure_code
        for result in results
        for finding in result.findings
        if finding.failure_code is not None
    ]


def test_wrong_boundary_decision_is_critical() -> None:
    case = CASES["ADDR_CHANGE_060"]
    run = make_run(
        case_id=case.case_id,
        decision="NOT_ELIGIBLE",
        answer="The window expired, so it is too late.",
        retrieved=["shipping_v1#address-change-window"],
        cited=["shipping_v1#address-change-window"],
        tools=["get_order"],
    )

    result = evaluate_case(case, run)

    assert result.passed is False
    assert result.critical_failures
    assert "WRONG_DECISION" in failure_codes([result])
    assert "FORBIDDEN_CLAIM" in failure_codes([result])


def test_fabricated_citation_and_retrieval_miss_are_separate_failures() -> None:
    case = CASES["ADDR_CHANGE_045"]
    run = make_run(
        case_id=case.case_id,
        decision="ELIGIBLE",
        answer="You're within the 60-minute window, so it's eligible.",
        retrieved=[],
        cited=["shipping_v1#address-change-window"],
        tools=["get_order", "update_address"],
    )

    result = evaluate_case(case, run)
    codes = failure_codes([result])

    assert "RETRIEVAL_MISS" in codes
    assert "FABRICATED_CITATION" in codes
