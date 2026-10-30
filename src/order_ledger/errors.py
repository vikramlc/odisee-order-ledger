class LedgerError(Exception):
    """Base class for order ledger errors."""


class ValidationError(LedgerError):
    """The request is malformed (empty items, bad quantity, bad limit...)."""


class OrderNotFound(LedgerError):
    """No order with that id exists for the customer."""


class InvalidCursor(LedgerError):
    """A pagination cursor could not be decoded or does not belong to the request."""


class IdempotencyConflict(LedgerError):
    """The idempotency key was already used with a different request body."""
