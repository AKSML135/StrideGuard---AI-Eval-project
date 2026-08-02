"""Compare two labelers' CSVs and report per-criterion agreement.

Usage:
    uv run python scripts/agreement_report.py \\
      --labeler-a evals/human_labels/labeler_a.csv \\
      --labeler-b evals/human_labels/labeler_b.csv
"""

import argparse
import csv
from pathlib import Path

from strideguard.metrics import agreement_report

CRITERIA = [
    "policy_correctness",
    "groundedness",
    "privacy_and_authorization",
    "action_integrity",
    "overall_pass",
]


def read_labels(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {f"{row['case_id']}::{row['run_id']}": row for row in reader}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labeler-a", type=Path, required=True)
    parser.add_argument("--labeler-b", type=Path, required=True)
    args = parser.parse_args()

    labels_a = read_labels(args.labeler_a)
    labels_b = read_labels(args.labeler_b)
    shared_keys = sorted(set(labels_a) & set(labels_b))

    if not shared_keys:
        print("No shared case_id/run_id rows between the two labelers.")
        return

    print(f"Comparing {len(shared_keys)} shared rows.\n")
    for criterion in CRITERIA:
        a_values = [labels_a[key][criterion] for key in shared_keys]
        b_values = [labels_b[key][criterion] for key in shared_keys]
        report = agreement_report(a_values, b_values)
        print(
            f"{criterion}: exact_agreement={report['exact_agreement']:.3f} "
            f"cohen_kappa={report['cohen_kappa']:.3f}"
        )


if __name__ == "__main__":
    main()
