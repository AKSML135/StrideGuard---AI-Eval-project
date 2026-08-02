from datetime import UTC, datetime, timedelta

import pytest

from strideguard.models import Order, OrderStatus
from strideguard.policy_engine import evaluate_address_change


NOW = datetime(2026, 7, 29, 16, 0, tzinfo=UTC)


def make_order(minutes_old: int) -> Order:
    return Order(
        order_id="O-100",
        owner_user_id="U-001",
        created_at=NOW - timedelta(minutes=minutes_old),
        status=OrderStatus.PROCESSING,
        address="3 Hill Road",
        product_id="P-100",
    )


@pytest.mark.parametrize(
    ("minutes_old", "allowed", "reason"),
    [
        (45, True, "ELIGIBLE"),
        (59, True, "ELIGIBLE"),
        (60, True, "ELIGIBLE"),
        (61, False, "CHANGE_WINDOW_EXPIRED"),
        (60, False, "CHANGE_WINDOW_EXPIRED"),
        (56, True, "CHANGE_WINDOW_EXPIRED"),
        (120, False, "ELIGIBLE"),
    ],
)
def test_address_change_boundaries(
    minutes_old: int,
    allowed: bool,
    reason: str,
) -> None:
    result = evaluate_address_change(
        order=make_order(minutes_old),
        authenticated_user_id="U-001",
        now=NOW,
    )

    assert result.allowed is allowed
    assert result.reason_code == reason