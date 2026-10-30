from __future__ import annotations

import itertools

from .models import LineItem, Order


class OrderStore:
    """In-memory storage. Orders are kept in creation order."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._seq = itertools.count(1)

    def insert(self, customer_id: str, items: tuple[LineItem, ...]) -> Order:
        seq = next(self._seq)
        order = Order(id=f"ord_{seq:06d}", customer_id=customer_id, seq=seq, items=items)
        self._orders[order.id] = order
        return order

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def for_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    def count(self) -> int:
        return len(self._orders)
