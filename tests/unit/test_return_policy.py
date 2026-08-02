from datetime import UTC, datetime, timedelta

import pytest

from strideguard.models import ProductCondition
from strideguard.policy_engine import evaluate_return


NOW = datetime(2026, 7, 29, 16, 0, tzinfo=UTC)


def delivered(days_old: int) -> datetime:
    return NOW - timedelta(days=days_old)


@pytest.mark.parametrize(
    (
        "days_old",
        "condition",
        "has_original_box",
        "allowed",
        "reason",
        "requires_escalation",
    ),
    [
        # Eligible
        (
            10,
            ProductCondition.UNOPENED,
            True,
            True,
            "ELIGIBLE",
            False,
        ),
        (
            30,
            ProductCondition.TRIED_ON,
            True,
            True,
            "ELIGIBLE",
            False,
        ),
        (
            15,
            ProductCondition.LIGHTLY_USED,
            True,
            True,
            "ELIGIBLE",
            False,
        ),

        # Return window expired
        (
            31,
            ProductCondition.UNOPENED,
            True,
            False,
            "RETURN_WINDOW_EXPIRED",
            False,
        ),

        # Item condition
        (
            5,
            ProductCondition.HEAVILY_USED,
            True,
            False,
            "ITEM_HEAVILY_USED",
            False,
        ),

        # Packaging requires escalation
        (
            15,
            ProductCondition.UNOPENED,
            False,
            False,
            "PACKAGING_POLICY_UNSPECIFIED",
            True,
        ),

        # Unknown packaging is still eligible
        (
            15,
            ProductCondition.UNOPENED,
            None,
            True,
            "ELIGIBLE",
            False,
        ),

        # First failing rule wins (return window checked first)
        (
            35,
            ProductCondition.HEAVILY_USED,
            False,
            False,
            "RETURN_WINDOW_EXPIRED",
            False,
        ),
    ],
)
def test_return_policy(
    days_old: int,
    condition: ProductCondition,
    has_original_box: bool | None,
    allowed: bool,
    reason: str,
    requires_escalation: bool,
) -> None:
    result = evaluate_return(
        delivered_at=delivered(days_old),
        now=NOW,
        condition=condition,
        has_original_box=has_original_box,
    )

    assert result.allowed is allowed
    assert result.reason_code == reason
    assert result.requires_escalation is requires_escalation