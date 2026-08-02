from datetime import datetime
from typing import Any

from strideguard.db import OrderRepository
from strideguard.policy_engine import evaluate_address_change


def get_order_action(
    *,
    repository: OrderRepository,
    authenticated_user_id: str,
    order_id: str,
) -> dict[str, Any]:
    order = repository.get_order(order_id)
    if order is None or order.owner_user_id != authenticated_user_id:
        return {
            "ok": False,
            "code": "ORDER_NOT_FOUND_OR_UNAUTHORIZED",
        }

    return {
        "ok": True,
        "order": {
            "order_id": order.order_id,
            "created_at": order.created_at.isoformat(),
            "status": order.status.value,
            "address": order.address,
            "product_id": order.product_id,
        },
    }


# Use the same public error code for missing and unauthorized orders.
# Otherwise, the error message can leak whether another user's order exists.


# The address action first loads the order, then calls the deterministic
# policy engine, then changes state.
def update_address_action(
    *,
    repository: OrderRepository,
    authenticated_user_id: str,
    order_id: str,
    new_address: str,
    now: datetime,
) -> dict[str, Any]:
    order = repository.get_order(order_id)
    if order is None:
        return {"ok": False, "code": "ORDER_NOT_FOUND_OR_UNAUTHORIZED"}

    decision = evaluate_address_change(
        order=order,
        authenticated_user_id=authenticated_user_id,
        now=now,
    )
    if not decision.allowed:
        public_code = (
            "ORDER_NOT_FOUND_OR_UNAUTHORIZED"
            if decision.reason_code == "UNAUTHORIZED_USER"
            else decision.reason_code
        )
        return {"ok": False, "code": public_code}

    changed = repository.update_address(order_id, new_address)
    return {
        "ok": changed,
        "code": "ADDRESS_UPDATED" if changed else "UPDATE_FAILED",
        "order_id": order_id if changed else None,
        "new_address": new_address if changed else None,
    }


# The LLM does not decide whether the user is authorized or whether 60
# minutes has elapsed. It asks the action layer, which returns a result.
