"""Hidden verifier for Task 2 (fail-to-pass). Do not read before solving."""

import pytest

from order_ledger import IdempotencyConflict, OrderService, ValidationError

ITEMS = [{"sku": "A", "quantity": 2, "unit_price_cents": 300}]
OTHER = [{"sku": "B", "quantity": 1, "unit_price_cents": 900}]


def test_replay_returns_original_and_stores_once():
    s = OrderService()
    first = s.create_order("c1", ITEMS, idempotency_key="k1")
    again = s.create_order("c1", ITEMS, idempotency_key="k1")
    assert again.id == first.id
    assert s.store.count() == 1


def test_replay_with_equal_but_new_dicts():
    s = OrderService()
    first = s.create_order("c1", [dict(ITEMS[0])], idempotency_key="k1")
    again = s.create_order("c1", [{"unit_price_cents": 300, "sku": "A", "quantity": 2}], idempotency_key="k1")
    assert again.id == first.id


def test_same_key_different_items_conflicts():
    s = OrderService()
    s.create_order("c1", ITEMS, idempotency_key="k1")
    with pytest.raises(IdempotencyConflict):
        s.create_order("c1", OTHER, idempotency_key="k1")
    assert s.store.count() == 1


def test_keys_are_scoped_per_customer():
    s = OrderService()
    a = s.create_order("c1", ITEMS, idempotency_key="k1")
    b = s.create_order("c2", ITEMS, idempotency_key="k1")
    assert a.id != b.id
    assert s.store.count() == 2


def test_different_keys_create_separate_orders():
    s = OrderService()
    a = s.create_order("c1", ITEMS, idempotency_key="k1")
    b = s.create_order("c1", ITEMS, idempotency_key="k2")
    assert a.id != b.id


def test_failed_validation_does_not_reserve_key():
    s = OrderService()
    with pytest.raises(ValidationError):
        s.create_order("c1", [], idempotency_key="k1")
    order = s.create_order("c1", OTHER, idempotency_key="k1")
    assert order.total_cents == 900
