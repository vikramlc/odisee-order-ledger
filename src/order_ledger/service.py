from __future__ import annotations

from collections.abc import Iterable

from .errors import OrderNotFound, ValidationError
from .models import LineItem, Order
from .store import OrderStore

MAX_ITEMS_PER_ORDER = 50


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
