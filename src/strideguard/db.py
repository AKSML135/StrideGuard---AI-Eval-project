"""A disposable SQLite repository for the sandboxed action agent.

NOTE: the guide prints the SQL schema, the method list
(initialize/reset/seed_order/get_order/update_address/create_escalation/snapshot),
and a two-line skeleton of `update_address` with a comment saying "execute the
update and return whether exactly one row changed" in place of real SQL. Every
method body below is reconstructed to match that schema and description.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from strideguard.models import Order

# get_order()/seed_order() use the typed `Order` model (not a raw dict) because
# Phase 10's actions.py accesses `order.owner_user_id`, `order.status.value`,
# and `order.created_at.isoformat()` as attributes on the returned object.

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    address TEXT NOT NULL,
    product_id TEXT NOT NULL,
    delivered_at TEXT
);

CREATE TABLE IF NOT EXISTS escalations (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    order_id TEXT,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class OrderRepository:
    def __init__(self, db_path: Path, *, fail_updates: bool = False):
        self.db_path = db_path
        self.fail_updates = fail_updates
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def reset(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM orders")
            connection.execute("DELETE FROM escalations")

    def seed_order(self, order: Order) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO orders (
                    order_id, owner_user_id, created_at, status,
                    address, product_id, delivered_at
                ) VALUES (:order_id, :owner_user_id, :created_at, :status,
                          :address, :product_id, :delivered_at)
                """,
                {
                    "order_id": order.order_id,
                    "owner_user_id": order.owner_user_id,
                    "created_at": order.created_at.isoformat(),
                    "status": order.status.value,
                    "address": order.address,
                    "product_id": order.product_id,
                    "delivered_at": (
                        order.delivered_at.isoformat() if order.delivered_at else None
                    ),
                },
            )

    def get_order(self, order_id: str) -> Order | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM orders WHERE order_id = ?", (order_id,)
            ).fetchone()
            return Order.model_validate(dict(row)) if row is not None else None

    def update_address(self, order_id: str, new_address: str) -> bool:
        if self.fail_updates:
            return False
        # Execute the update and return whether exactly one row changed.
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE orders SET address = ? WHERE order_id = ?",
                (new_address, order_id),
            )
            return cursor.rowcount == 1

    def create_escalation(
        self,
        *,
        user_id: str,
        order_id: str | None,
        reason: str,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO escalations (user_id, order_id, reason, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, order_id, reason, datetime.utcnow().isoformat()),
            )
            return int(cursor.lastrowid)

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as connection:
            orders = [
                dict(row)
                for row in connection.execute("SELECT * FROM orders").fetchall()
            ]
            escalations = [
                dict(row)
                for row in connection.execute("SELECT * FROM escalations").fetchall()
            ]
        return {"orders": orders, "escalations": escalations}
