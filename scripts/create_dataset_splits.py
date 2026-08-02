"""Split a reviewed dataset into development and holdout sets.

Refuses to create a holdout from fewer than 40 cases.

Usage:
    uv run python scripts/create_dataset_splits.py \\
      --dataset evals/datasets/all_reviewed.jsonl \\
      --dev-output evals/datasets/dev_v2.jsonl \\
      --holdout-output evals/datasets/holdout_v2.jsonl \\
      --holdout-fraction 0.25 \\
      --seed 42
"""

import argparse
import random
from pathlib import Path

from strideguard.datasets import load_cases, write_jsonl

MINIMUM_CASES_FOR_HOLDOUT = 40


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dev-output", type=Path, required=True)
    parser.add_argument("--holdout-output", type=Path, required=True)
    parser.add_argument("--holdout-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    if len(cases) < MINIMUM_CASES_FOR_HOLDOUT:
        raise SystemExit(
            f"Refusing to create a holdout from {len(cases)} cases "
            f"(minimum is {MINIMUM_CASES_FOR_HOLDOUT})."
        )

    ordered = sorted(cases, key=lambda case: case.case_id)
    rng = random.Random(args.seed)
    rng.shuffle(ordered)

    holdout_size = round(len(ordered) * args.holdout_fraction)
    holdout = ordered[:holdout_size]
    dev = ordered[holdout_size:]

    write_jsonl(args.dev_output, dev)
    write_jsonl(args.holdout_output, holdout)

    print(f"Development set: {len(dev)} cases -> {args.dev_output}")
    print(f"Holdout set: {len(holdout)} cases -> {args.holdout_output}")


if __name__ == "__main__":
    main()
