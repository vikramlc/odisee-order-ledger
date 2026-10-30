# odisee-order-ledger

A small, original practice repository for **Odisee** AI-assisted coding mocks.
It is a slice of an order service: an in-memory store, a service layer with
validation, and a pytest suite. No web framework, no database, no network.

Licence: MIT (see `LICENSE`).

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) (or plain `pip install pytest`).

```bash
uv run pytest -q          # or: python -m pytest -q
```

All tests pass on `main`.

## Layout

| Path | What it is |
|---|---|
| `src/order_ledger/models.py` | `Order` and `LineItem` dataclasses (`Order.seq` is a global, strictly increasing creation number) |
| `src/order_ledger/store.py` | `OrderStore`: in-memory dict, assigns ids and `seq` |
| `src/order_ledger/service.py` | `OrderService`: `create_order`, `get_order`, `list_orders` |
| `src/order_ledger/errors.py` | Error types, including `InvalidCursor` and `IdempotencyConflict` (defined, not yet used) |
| `tests/` | The visible test suite |

## Tasks

Each task is graded on its own, starting from `main`. Work with any AI
assistant you like, but you own the result: read every edit, run the tests,
and do not change existing tests to make them pass.

### Task 1 — cursor pagination (`t1-pagination`)

`list_orders` returns every order of a customer at once. Add

```python
OrderService.list_orders_page(customer_id, limit=50, cursor=None) -> Page
```

* `Page` is a small dataclass with `items: list[Order]` and `next_cursor: str | None`.
* Orders are returned oldest first (by `seq`), only for that customer.
* `limit` must be between 1 and 200 inclusive, otherwise raise `ValidationError`.
* `next_cursor` is an opaque string; pass it back to get the next page. It is
  `None` on the last page.
* Following the cursors from the first page returns every order exactly once,
  even if new orders are created between page requests (new orders appear at the end).
* A cursor that cannot be decoded, or that was issued for another customer,
  raises `InvalidCursor`.
* `list_orders` keeps working exactly as before.

Add tests for the first page, a middle page, the last page and the error cases.

### Task 2 — idempotent order creation (`t2-idempotency`)

Clients retry `create_order` on timeouts and create duplicate orders. Add an
optional `idempotency_key: str | None = None` argument to `create_order`.

* Same customer + same key + same items: return the **original** order; no new order is stored.
* Same customer + same key + different items: raise `IdempotencyConflict`.
* Keys are scoped per customer: another customer may use the same key.
* `idempotency_key=None` behaves exactly as today.
* A request that fails validation must not reserve the key.

Add tests for each rule.

## For graders

* Golden solutions: branches `solution/t1-pagination` and `solution/t2-idempotency`.
* Hidden verifier tests: branch `verifier`, directory `verifier/`.
  * fail-to-pass: `verifier/test_t1_pagination.py`, `verifier/test_t2_idempotency.py`
    (fail on `main`, pass on the golden solution).
  * pass-to-pass: the `tests/` directory **as it is on `main`** (restore it before
    running, so edited tests cannot hide a regression).

```bash
git checkout <candidate>
git checkout main -- tests/
git checkout verifier -- verifier/
uv run pytest -q verifier/test_t1_pagination.py   # fail-to-pass
uv run pytest -q tests                            # pass-to-pass
```

Please solve the tasks before looking at those branches.
