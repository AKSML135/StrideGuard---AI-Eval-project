"""Summarize pilot user feedback.

Usage:
    uv run python scripts/summarize_feedback.py \\
      --feedback artifacts/user_feedback/pilot_feedback.csv
"""

import argparse
import csv
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    with args.feedback.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        print("No feedback rows found.")
        return

    total = len(rows)
    thumbs_up = sum(1 for row in rows if row.get("rating") == "up")
    categories = Counter(row.get("reason_category", "unknown") for row in rows)
    tasks = Counter(row.get("task_id", "unknown") for row in rows)
    completed_by_task = Counter(
        row.get("task_id", "unknown")
        for row in rows
        if row.get("task_completed", "").lower() in {"true", "1", "yes"}
    )
    critical = [row for row in rows if row.get("reason_category") == "Agent should have escalated"]
    disagreements = [
        row
        for row in rows
        if row.get("rating") == "down"
        and row.get("reason_category") == "Policy was disappointing but response was correct"
    ]

    print(f"Total interactions: {total}")
    print(f"Thumbs-up rate: {thumbs_up / total:.1%}")
    print("\nCompletion rate by task:")
    for task_id, count in sorted(tasks.items()):
        completed = completed_by_task.get(task_id, 0)
        print(f"  {task_id}: {completed}/{count} ({completed / count:.0%})")
    print("\nFeedback categories:")
    for category, count in categories.most_common():
        print(f"  {category}: {count}")
    print(f"\nPotential critical incidents (should have escalated): {len(critical)}")
    print(
        "User dislike but policy was correct "
        f"(user-satisfaction vs. correctness disagreement): {len(disagreements)}"
    )


if __name__ == "__main__":
    main()
