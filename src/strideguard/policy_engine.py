from datetime import datetime

from strideguard.models import Decision, Order, OrderStatus, ProductCondition

ADDRESS_CHANGE_WINDOW_MINUTES = 60
RETURN_WINDOW_DAYS = 30


def elapsed_minutes(created_at: datetime, now: datetime) -> float:
    if created_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("created_at and now must be timezone-aware")
    if now < created_at:
        raise ValueError("now cannot be earlier than created_at")
    return (now - created_at).total_seconds() / 60


def evaluate_address_change(
    *,
    order: Order,
    authenticated_user_id: str,
    now: datetime,
) -> Decision:
    if authenticated_user_id != order.owner_user_id:
        return Decision(
            allowed=False,
            reason_code="UNAUTHORIZED_USER",
            explanation="The authenticated user does not own this order.",
        )

    if order.status is not OrderStatus.PROCESSING:
        return Decision(
            allowed=False,
            reason_code="ORDER_NOT_PROCESSING",
            explanation="Only processing orders can have their address changed.",
        )

    age = elapsed_minutes(order.created_at, now)
    if age > ADDRESS_CHANGE_WINDOW_MINUTES:
        return Decision(
            allowed=False,
            reason_code="CHANGE_WINDOW_EXPIRED",
            explanation=f"The order is {age:.1f} minutes old, beyond the window.",
        )

    return Decision(
        allowed=True,
        reason_code="ELIGIBLE",
        explanation=f"The order is {age:.1f} minutes old and still processing.",
    )


# The comparison is > 60, not >= 60, because exactly 60 minutes is eligible.


def evaluate_return(
    *,
    delivered_at: datetime,
    now: datetime,
    condition: ProductCondition,
    has_original_box: bool | None,
) -> Decision:
    age_days = (now - delivered_at).total_seconds() / 86_400

    if age_days > RETURN_WINDOW_DAYS:
        return Decision(
            allowed=False,
            reason_code="RETURN_WINDOW_EXPIRED",
            explanation="The request is beyond the 30-day window.",
        )

    if condition is ProductCondition.HEAVILY_USED:
        return Decision(
            allowed=False,
            reason_code="ITEM_HEAVILY_USED",
            explanation="Heavily used products are not eligible.",
        )

    if has_original_box is False:
        return Decision(
            allowed=False,
            reason_code="PACKAGING_POLICY_UNSPECIFIED",
            explanation="The policy does not define eligibility without packaging.",
            requires_escalation=True,
        )

    return Decision(
        allowed=True,
        reason_code="ELIGIBLE",
        explanation="The time window and condition requirements are satisfied.",
    )
