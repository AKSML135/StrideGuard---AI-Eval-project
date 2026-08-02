from collections.abc import Sequence
from typing import Any

from sklearn.metrics import (
    cohen_kappa_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def exact_agreement(labels_a: Sequence[Any], labels_b: Sequence[Any]) -> float:
    if len(labels_a) != len(labels_b):
        raise ValueError("Label sequences must have equal length")
    if not labels_a:
        return 0.0
    return sum(
        a == b for a, b in zip(labels_a, labels_b, strict=True)
    ) / len(labels_a)


def agreement_report(
    labels_a: Sequence[str],
    labels_b: Sequence[str],
) -> dict[str, float]:
    return {
        "exact_agreement": exact_agreement(labels_a, labels_b),
        "cohen_kappa": float(cohen_kappa_score(labels_a, labels_b)),
    }


# The important positive class for judge calibration is failure detection.
def binary_judge_report(
    human_pass: Sequence[bool],
    judge_pass: Sequence[bool],
) -> dict[str, object]:
    human_fail = [not value for value in human_pass]
    judge_fail = [not value for value in judge_pass]

    precision, recall, f1, _ = precision_recall_fscore_support(
        human_fail,
        judge_fail,
        average="binary",
        zero_division=0,
    )
    matrix = confusion_matrix(
        human_fail,
        judge_fail,
        labels=[False, True],
    ).tolist()

    return {
        "agreement": exact_agreement(human_pass, judge_pass),
        "failure_precision": float(precision),
        "failure_recall": float(recall),
        "failure_f1": float(f1),
        "confusion_matrix_good_fail": matrix,
    }


# Interpretation:
#   Failure precision: when the judge says fail, how often is the human label
#   also fail?
#   Failure recall: of all human-labeled failures, how many did the judge catch?
#   Critical false negative: the human says a critical failure occurred, but
#   the judge approves the response.
#
# For safety and authorization, critical false negatives matter more than
# headline agreement.
