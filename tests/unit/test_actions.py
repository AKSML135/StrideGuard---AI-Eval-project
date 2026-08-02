"""Unit tests for the action layer.

NOTE: the guide prints both test bodies verbatim but relies on two helpers,
`seed_repository` and `make_order`, whose implementations were never shown.
They are reconstructed below following the same pattern used in
tests/unit/test_policy_engine.py.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from strideguard.actions import update_address_action
from strideguard.db import OrderRepository
from strideguard.models import Order, OrderStatus

NOW = datetime(2026, 7, 29, 16, 0, tzinfo=UTC)


def make_order(
    order_id: str,
    *,
    minutes_old: int,
    owner_user_id: str = "U-001",
    address: str = "5 Cedar Road",
    status: OrderStatus = OrderStatus.PROCESSING,
) -> Order:
    return Order(
        order_id=order_id,
        owner_user_id=owner_user_id,
        created_at=NOW - timedelta(minutes=minutes_old),
        status=status,
        address=address,
        product_id="P-100",
    )


def seed_repository(tmp_path: Path, *, minutes_old: int) -> OrderRepository:
    repository = OrderRepository(tmp_path / "orders.sqlite")
    repository.seed_order(make_order("O-100", minutes_old=minutes_old))
    return repository


def test_update_address_changes_state_when_policy_allows(tmp_path: Path) -> None:
    repository = seed_repository(tmp_path, minutes_old=60)

    result = update_address_action(
        repository=repository,
        authenticated_user_id="U-001",
        order_id="O-100",
        new_address="8 Lake Street",
        now=NOW,
    )

    assert result["ok"] is True
    assert repository.get_order("O-100").address == "8 Lake Street"


def test_fault_injected_update_preserves_state(tmp_path: Path) -> None:
    repository = OrderRepository(
        tmp_path / "failed.sqlite",
        fail_updates=True,
    )
    repository.seed_order(make_order("O-130", minutes_old=30))

    result = update_address_action(
        repository=repository,
        authenticated_user_id="U-001",
        order_id="O-130",
        new_address="10 Birch Court",
        now=NOW,
    )

    assert result["ok"] is False
    assert result["code"] == "UPDATE_FAILED"
    assert repository.get_order("O-130").address == "5 Cedar Road"
