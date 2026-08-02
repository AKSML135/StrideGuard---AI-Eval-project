"""Run deterministic evaluators over a frozen run file.

Usage:
    uv run python scripts/run_deterministic_evals.py \\
      --dataset evals/datasets/dev.jsonl \\
      --runs artifacts/runs/agent_v1.jsonl \\
      --output artifacts/eval_reports/agent_v1.json

Exits non-zero when any critical failure is present, so it can act as a CI
release gate.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from strideguard.datasets import load_cases
from strideguard.evaluators import evaluate_case
from strideguard.models import RunRecord


def load_runs(path: Path) -> list[RunRecord]:
    runs = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                runs.append(RunRecord.model_validate_json(line))
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases_by_id = {case.case_id: case for case in load_cases(args.dataset)}
    runs = load_runs(args.runs)

    results = []
    failure_counter: Counter[str] = Counter()
    critical_failures = []

    for run in runs:
        case = cases_by_id.get(run.case_id)
        if case is None:
            continue
        result = evaluate_case(case, run)
        results.append(result)
        for finding in result.findings:
            if finding.failure_code:
                failure_counter[finding.failure_code] += 1
        if result.critical_failures:
            critical_failures.append(run.case_id)

    passed = sum(1 for result in results if result.passed)
    report = {
        "total_cases": len(results),
        "passed": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "critical_failure_cases": critical_failures,
        "failure_code_counts": dict(failure_counter),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))

    if critical_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
