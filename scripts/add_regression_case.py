"""Promote a reviewed case into the critical regression file.

Usage:
    uv run python scripts/add_regression_case.py \\
      --source evals/datasets/dev_v2.jsonl \\
      --case-id FALSE_SUCCESS_UPDATE_FAILURE \\
      --regression-file evals/datasets/critical_regression.jsonl
"""

import argparse
from pathlib import Path

from strideguard.datasets import load_cases, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--regression-file", type=Path, required=True)
    args = parser.parse_args()

    source_cases = {case.case_id: case for case in load_cases(args.source)}
    if args.case_id not in source_cases:
        raise SystemExit(f"Case {args.case_id!r} not found in {args.source}")

    existing = (
        load_cases(args.regression_file) if args.regression_file.exists() else []
    )
    existing_ids = {case.case_id for case in existing}

    if args.case_id in existing_ids:
        print(f"Case {args.case_id!r} is already in the regression file.")
        return

    existing.append(source_cases[args.case_id])
    write_jsonl(args.regression_file, existing)
    print(f"Added {args.case_id!r} to {args.regression_file}")


if __name__ == "__main__":
    main()
