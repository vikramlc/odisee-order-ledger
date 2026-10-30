import pytest

from order_ledger import OrderNotFound, OrderService, ValidationError


def item(sku="SKU-1", quantity=1, price=500):
    return {"sku": sku, "quantity": quantity, "unit_price_cents": price}


@pytest.fixture
def service():
    return OrderService()


def test_create_order_totals(service):
    order = service.create_order("cus_1", [item(quantity=2, price=250), item("SKU-2", 1, 100)])
    assert order.customer_id == "cus_1"
    assert order.total_cents == 600
    assert order.id.startswith("ord_")


def test_create_order_rejects_empty(service):
    with pytest.raises(ValidationError):
        service.create_order("cus_1", [])


def test_create_order_rejects_bad_quantity(service):
    with pytest.raises(ValidationError):
        service.create_order("cus_1", [item(quantity=0)])


def test_create_order_requires_customer(service):
    with pytest.raises(ValidationError):
        service.create_order("", [item()])


def test_get_order_other_customer_is_not_found(service):
    order = service.create_order("cus_1", [item()])
    with pytest.raises(OrderNotFound):
        service.get_order("cus_2", order.id)


def test_list_orders_oldest_first_and_scoped(service):
    a = service.create_order("cus_1", [item()])
    service.create_order("cus_2", [item()])
    b = service.create_order("cus_1", [item()])
    assert [o.id for o in service.list_orders("cus_1")] == [a.id, b.id]


def test_ids_are_unique(service):
    ids = {service.create_order("cus_1", [item()]).id for _ in range(20)}
    assert len(ids) == 20
