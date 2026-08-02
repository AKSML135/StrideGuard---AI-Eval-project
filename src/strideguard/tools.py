"""Wrap the action layer as LangChain tools.

NOTE: the guide shows `get_order` and `update_address` as free-standing
`@tool`-decorated functions that close over `repository`, `authenticated_user_id`,
`now_provider`, and a `record` helper -- but those names have to come from
somewhere. Reconstructed here as a `build_tools(...)` factory that creates a
fresh, per-request closure over exactly those values (repository, user, and a
now() provider), plus a `record` helper that appends a ToolCallRecord to a
shared list so the agent's tool-call trace can be inspected afterward.
"""

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from langchain.tools import tool

from strideguard.actions import get_order_action, update_address_action
from strideguard.db import OrderRepository
from strideguard.models import ToolCallRecord


def build_tools(
    *,
    repository: OrderRepository,
    authenticated_user_id: str,
    now_provider: Callable[[], datetime],
    tool_calls: list[ToolCallRecord],
) -> list[Any]:
    def record(name: str, arguments: dict[str, Any], result: dict[str, Any]) -> str:
        tool_calls.append(
            ToolCallRecord(
                name=name,
                arguments=arguments,
                result=json.dumps(result) if result.get("ok") else None,
                error=None if result.get("ok") else result.get("code"),
            )
        )
        return json.dumps(result)

    @tool
    def get_order(order_id: str) -> str:
        """Get the authenticated customer's order. Never inspect another user."""
        result = get_order_action(
            repository=repository,
            authenticated_user_id=authenticated_user_id,
            order_id=order_id,
        )
        return record("get_order", {"order_id": order_id}, result)

    @tool
    def update_address(order_id: str, new_address: str) -> str:
        """Change a processing order address only when deterministic policy permits."""
        result = update_address_action(
            repository=repository,
            authenticated_user_id=authenticated_user_id,
            order_id=order_id,
            new_address=new_address,
            now=now_provider(),
        )
        return record(
            "update_address",
            {"order_id": order_id, "new_address": new_address},
            result,
        )

    return [get_order, update_address]
