from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterable
from dataclasses import dataclass

from .errors import InvalidCursor, OrderNotFound, ValidationError
from .models import LineItem, Order
from .store import OrderStore

MAX_ITEMS_PER_ORDER = 50
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class Page:
    items: list[Order]
    next_cursor: str | None


class OrderService:
    def __init__(self, store: OrderStore | None = None) -> None:
        self.store = store or OrderStore()

    def create_order(self, customer_id: str, items: Iterable[dict]) -> Order:
        """Create an order from raw item dicts: {"sku", "quantity", "unit_price_cents"}."""
        if not customer_id:
            raise ValidationError("customer_id is required")
        line_items = tuple(self._line_item(raw) for raw in items)
        if not line_items:
            raise ValidationError("an order needs at least one item")
        if len(line_items) > MAX_ITEMS_PER_ORDER:
            raise ValidationError(f"at most {MAX_ITEMS_PER_ORDER} items per order")
        return self.store.insert(customer_id, line_items)

    def get_order(self, customer_id: str, order_id: str) -> Order:
        order = self.store.get(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderNotFound(order_id)
        return order

    def list_orders(self, customer_id: str) -> list[Order]:
        """All orders of a customer, oldest first."""
        return sorted(self.store.for_customer(customer_id), key=lambda o: o.seq)

    def list_orders_page(self, customer_id: str, limit: int = DEFAULT_PAGE_SIZE, cursor: str | None = None) -> Page:
        """One page of a customer's orders, oldest first. Keyset pagination on `seq`."""
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise ValidationError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
        after = _decode_cursor(cursor, customer_id) if cursor is not None else 0
        newer = [o for o in self.list_orders(customer_id) if o.seq > after]
        items = newer[:limit]
        has_more = len(newer) > limit
        next_cursor = _encode_cursor(customer_id, items[-1].seq) if has_more else None
        return Page(items=items, next_cursor=next_cursor)

    @staticmethod
    def _line_item(raw: dict) -> LineItem:
        try:
            sku = str(raw["sku"]).strip()
            quantity = int(raw["quantity"])
            price = int(raw["unit_price_cents"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"bad item: {raw!r}") from exc
        if not sku or quantity < 1 or price < 0:
            raise ValidationError(f"bad item: {raw!r}")
        return LineItem(sku=sku, quantity=quantity, unit_price_cents=price)


def _encode_cursor(customer_id: str, seq: int) -> str:
    raw = json.dumps({"c": customer_id, "s": seq}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode_cursor(cursor: str, customer_id: str) -> int:
    try:
        body = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        owner, seq = body["c"], body["s"]
    except (binascii.Error, ValueError, KeyError, TypeError) as exc:
        raise InvalidCursor("cursor cannot be decoded") from exc
    if owner != customer_id or not isinstance(seq, int) or seq < 0:
        raise InvalidCursor("cursor does not belong to this request")
    return seq
