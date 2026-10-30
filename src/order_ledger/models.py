from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int
    unit_price_cents: int

    @property
    def total_cents(self) -> int:
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class Order:
    id: str
    customer_id: str
    seq: int  # global creation sequence, strictly increasing
    items: tuple[LineItem, ...] = field(default_factory=tuple)

    @property
    def total_cents(self) -> int:
        return sum(item.total_cents for item in self.items)
