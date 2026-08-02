"""Export frozen runs to a CSV template for human labeling.

Usage:
    uv run python scripts/export_for_labeling.py \\
      --dataset evals/datasets/dev.jsonl \\
      --runs artifacts/runs/baseline_v1.jsonl \\
      --output evals/human_labels/baseline_labeling_template.csv
"""

import argparse
import csv
from pathlib import Path

from strideguard.datasets import load_cases
from strideguard.models import RunRecord

COLUMNS = [
    "case_id",
    "run_id",
    "description",
    "user_input",
    "expected_behavior",
    "candidate_response",
    "candidate_decision",
    "retrieved_doc_ids",
    "tool_calls",
    "labeler_id",
    "rubric_version",
    "policy_correctness",
    "groundedness",
    "privacy_and_authorization",
    "action_integrity",
    "task_completion",
    "actionability",
    "conciseness",
    "tone",
    "overall_pass",
    "failure_codes",
    "evidence",
    "notes",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases_by_id = {case.case_id: case for case in load_cases(args.dataset)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle, args.runs.open(
        encoding="utf-8"
    ) as runs_file:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()

        for line in runs_file:
            if not line.strip():
                continue
            run = RunRecord.model_validate_json(line)
            case = cases_by_id.get(run.case_id)
            if case is None:
                continue

            writer.writerow(
                {
                    "case_id": run.case_id,
                    "run_id": run.run_id,
                    "description": case.description,
                    "user_input": case.user_input,
                    "expected_behavior": case.expected_behavior.model_dump_json(),
                    "candidate_response": run.response.answer if run.response else "",
                    "candidate_decision": run.response.decision if run.response else "",
                    "retrieved_doc_ids": ";".join(run.retrieved_doc_ids),
                    "tool_calls": ";".join(call.name for call in run.tool_calls),
                    "labeler_id": "",
                    "rubric_version": "1.0",
                    "policy_correctness": "",
                    "groundedness": "",
                    "privacy_and_authorization": "",
                    "action_integrity": "",
                    "task_completion": "",
                    "actionability": "",
                    "conciseness": "",
                    "tone": "",
                    "overall_pass": "",
                    "failure_codes": "",
                    "evidence": "",
                    "notes": "",
                }
            )

    print(f"Wrote labeling template to {args.output}")


if __name__ == "__main__":
    main()
