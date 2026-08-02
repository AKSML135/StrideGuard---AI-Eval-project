"""Calibrate the LLM judge against adjudicated human labels.

Usage:
    uv run python scripts/calibrate_judge.py \\
      --dataset evals/datasets/dev.jsonl \\
      --runs artifacts/runs/agent_v1.jsonl \\
      --human-labels evals/human_labels/adjudicated_gold.csv \\
      --rubric evals/rubrics/rubric_v1.yaml \\
      --output artifacts/eval_reports/judge_calibration_v1.json
"""

import argparse
import csv
import json
from pathlib import Path

from strideguard.datasets import load_cases
from strideguard.judge import JUDGE_PROMPT_VERSION, judge_run
from strideguard.llm_factory import build_chat_model
from strideguard.metrics import binary_judge_report
from strideguard.models import RunRecord
from strideguard.settings import get_settings


def load_runs(path: Path) -> dict[str, RunRecord]:
    runs = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                run = RunRecord.model_validate_json(line)
                runs[run.run_id] = run
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--human-labels", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    settings = get_settings()
    judge_model = build_chat_model(settings)
    rubric_text = args.rubric.read_text(encoding="utf-8")
    cases_by_id = {case.case_id: case for case in load_cases(args.dataset)}
    runs_by_id = load_runs(args.runs)

    human_pass: list[bool] = []
    judge_pass: list[bool] = []
    critical_false_negatives: list[str] = []
    disagreements: list[dict] = []

    with args.human_labels.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            case = cases_by_id.get(row["case_id"])
            run = runs_by_id.get(row["run_id"])
            if case is None or run is None:
                continue

            human_result = row["overall_pass"].strip().lower() in {"true", "1", "yes"}
            verdict = judge_run(
                case=case,
                run=run,
                rubric_text=rubric_text,
                judge_model=judge_model,
            )

            human_pass.append(human_result)
            judge_pass.append(verdict.overall_pass)

            if human_result != verdict.overall_pass:
                disagreements.append(
                    {
                        "case_id": row["case_id"],
                        "run_id": row["run_id"],
                        "human_overall_pass": human_result,
                        "judge_overall_pass": verdict.overall_pass,
                    }
                )
                if not human_result and verdict.overall_pass:
                    critical_false_negatives.append(row["case_id"])

    metrics = binary_judge_report(human_pass, judge_pass)
    report = {
        "judge_model": settings.selected_model,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "rubric_path": str(args.rubric),
        "num_examples": len(human_pass),
        **metrics,
        "critical_false_negative_cases": critical_false_negatives,
        "disagreements": disagreements,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
