"""Hidden verifier for Task 1 (fail-to-pass). Do not read before solving."""

import pytest

from order_ledger import InvalidCursor, OrderService, ValidationError


def make(service, customer, n):
    return [service.create_order(customer, [{"sku": f"S{i}", "quantity": 1, "unit_price_cents": 100}]) for i in range(n)]


def walk(service, customer, limit):
    seen, cursor, pages = [], None, 0
    while True:
        page = service.list_orders_page(customer, limit=limit, cursor=cursor)
        seen.extend(o.id for o in page.items)
        pages += 1
        if page.next_cursor is None:
            return seen, pages
        cursor = page.next_cursor
        assert pages < 100


def test_first_page_oldest_first():
    s = OrderService()
    orders = make(s, "c1", 5)
    page = s.list_orders_page("c1", limit=2)
    assert [o.id for o in page.items] == [orders[0].id, orders[1].id]
    assert page.next_cursor is not None


def test_walk_returns_every_order_once_and_scoped():
    s = OrderService()
    mine = []
    for i in range(7):
        mine += make(s, "c1", 1)
        make(s, "c2", 1)
    seen, pages = walk(s, "c1", 3)
    assert seen == [o.id for o in mine]
    assert pages == 3


def test_exact_multiple_has_no_empty_trailing_page():
    s = OrderService()
    make(s, "c1", 4)
    first = s.list_orders_page("c1", limit=2)
    second = s.list_orders_page("c1", limit=2, cursor=first.next_cursor)
    assert len(second.items) == 2
    assert second.next_cursor is None


def test_new_orders_during_paging_appear_at_end():
    s = OrderService()
    old = make(s, "c1", 3)
    first = s.list_orders_page("c1", limit=2)
    new = make(s, "c1", 2)
    rest = s.list_orders_page("c1", limit=10, cursor=first.next_cursor)
    assert [o.id for o in first.items + rest.items] == [o.id for o in old + new]


def test_default_limit_is_50():
    s = OrderService()
    make(s, "c1", 51)
    page = s.list_orders_page("c1")
    assert len(page.items) == 50
    assert page.next_cursor is not None


@pytest.mark.parametrize("limit", [0, -1, 201])
def test_limit_bounds(limit):
    s = OrderService()
    with pytest.raises(ValidationError):
        s.list_orders_page("c1", limit=limit)


def test_limit_200_allowed():
    s = OrderService()
    make(s, "c1", 3)
    assert len(s.list_orders_page("c1", limit=200).items) == 3


def test_garbage_cursor_rejected():
    s = OrderService()
    make(s, "c1", 3)
    with pytest.raises(InvalidCursor):
        s.list_orders_page("c1", limit=2, cursor="not-a-cursor!!")


def test_cursor_for_other_customer_rejected():
    s = OrderService()
    make(s, "c1", 3)
    make(s, "c2", 3)
    cursor = s.list_orders_page("c1", limit=1).next_cursor
    with pytest.raises(InvalidCursor):
        s.list_orders_page("c2", limit=1, cursor=cursor)


def test_empty_customer():
    s = OrderService()
    page = s.list_orders_page("nobody", limit=5)
    assert page.items == []
    assert page.next_cursor is None

