"""Validate a golden dataset JSONL file.

Usage:
    uv run python scripts/validate_dataset.py evals/datasets/dev.jsonl
"""

import sys
from pathlib import Path

from strideguard.datasets import load_cases, validate_case_ids, validate_dataset_coverage


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_dataset.py <path-to-jsonl>")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    cases = load_cases(path)
    validate_case_ids(cases)
    coverage = validate_dataset_coverage(cases)

    print(f"Valid cases: {len(cases)}")
    for key, count in coverage.items():
        print(f"{key} = {count}")


if __name__ == "__main__":
    main()
