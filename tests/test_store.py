from order_ledger import LineItem, OrderStore


def test_insert_assigns_increasing_seq():
    store = OrderStore()
    a = store.insert("cus_1", (LineItem("A", 1, 100),))
    b = store.insert("cus_1", (LineItem("B", 1, 100),))
    assert b.seq == a.seq + 1
    assert store.count() == 2


def test_for_customer_filters():
    store = OrderStore()
    store.insert("cus_1", (LineItem("A", 1, 100),))
    store.insert("cus_2", (LineItem("A", 1, 100),))
    assert len(store.for_customer("cus_1")) == 1
