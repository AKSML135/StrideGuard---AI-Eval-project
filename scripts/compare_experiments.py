"""Compare multiple frozen run files on pass rate, critical slices, and latency.

Usage:
    uv run python scripts/compare_experiments.py \\
      --dataset evals/datasets/dev.jsonl \\
      --runs \\
        artifacts/runs/baseline_v1.jsonl \\
        artifacts/runs/rag_v1.jsonl \\
        artifacts/runs/agent_v1.jsonl \\
      --output artifacts/eval_reports/experiment_comparison.json
"""

import argparse
import json
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


def summarize(path: Path, cases_by_id: dict) -> dict:
    runs = load_runs(path)
    results = [
        evaluate_case(cases_by_id[run.case_id], run)
        for run in runs
        if run.case_id in cases_by_id
    ]

    passed = sum(1 for result in results if result.passed)
    critical_slice = [
        result
        for result in results
        if cases_by_id[result.case_id].tags.get("critical")
    ]
    critical_passed = sum(1 for result in critical_slice if result.passed)
    critical_failure_count = sum(1 for result in results if result.critical_failures)
    error_count = sum(1 for run in runs if run.error)
    latencies = sorted(run.latency_ms for run in runs)

    failure_codes: Counter[str] = Counter()
    for result in results:
        for finding in result.findings:
            if finding.failure_code:
                failure_codes[finding.failure_code] += 1

    def percentile(values: list[float], fraction: float) -> float:
        if not values:
            return 0.0
        index = min(len(values) - 1, int(len(values) * fraction))
        return values[index]

    return {
        "run_file": str(path),
        "total_cases": len(runs),
        "pass_rate": passed / len(results) if results else 0.0,
        "critical_slice_pass_rate": (
            critical_passed / len(critical_slice) if critical_slice else None
        ),
        "critical_failure_count": critical_failure_count,
        "error_count": error_count,
        "p50_latency_ms": percentile(latencies, 0.5),
        "p95_latency_ms": percentile(latencies, 0.95),
        "failure_code_distribution": dict(failure_codes),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases_by_id = {case.case_id: case for case in load_cases(args.dataset)}
    summaries = [summarize(path, cases_by_id) for path in args.runs]

    report = {"experiments": summaries}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
