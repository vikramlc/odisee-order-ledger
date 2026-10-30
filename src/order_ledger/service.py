from __future__ import annotations

from collections.abc import Iterable

from .errors import IdempotencyConflict, OrderNotFound, ValidationError
from .models import LineItem, Order
from .store import OrderStore

MAX_ITEMS_PER_ORDER = 50


class OrderService:
    def __init__(self, store: OrderStore | None = None) -> None:
        self.store = store or OrderStore()
        # (customer_id, idempotency_key) -> (normalized items, order id)
        self._idempotency: dict[tuple[str, str], tuple[tuple[LineItem, ...], str]] = {}

    def create_order(self, customer_id: str, items: Iterable[dict], idempotency_key: str | None = None) -> Order:
        """Create an order from raw item dicts: {"sku", "quantity", "unit_price_cents"}.

        With an idempotency key, a retry with the same items returns the original
        order, and a reuse with different items raises IdempotencyConflict.
        """
        if not customer_id:
            raise ValidationError("customer_id is required")
        line_items = tuple(self._line_item(raw) for raw in items)
        if not line_items:
            raise ValidationError("an order needs at least one item")
        if len(line_items) > MAX_ITEMS_PER_ORDER:
            raise ValidationError(f"at most {MAX_ITEMS_PER_ORDER} items per order")
        if idempotency_key is None:
            return self.store.insert(customer_id, line_items)
        slot = (customer_id, idempotency_key)
        previous = self._idempotency.get(slot)
        if previous is not None:
            seen_items, order_id = previous
            if seen_items != line_items:
                raise IdempotencyConflict(idempotency_key)
            order = self.store.get(order_id)
            assert order is not None
            return order
        order = self.store.insert(customer_id, line_items)
        self._idempotency[slot] = (line_items, order.id)
        return order

    def get_order(self, customer_id: str, order_id: str) -> Order:
        order = self.store.get(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderNotFound(order_id)
        return order

    def list_orders(self, customer_id: str) -> list[Order]:
        """All orders of a customer, oldest first."""
        return sorted(self.store.for_customer(customer_id), key=lambda o: o.seq)

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
