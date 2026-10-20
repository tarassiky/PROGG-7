"""Предметная модель: два агрегата."""

from .errors import (
    CurrencyMismatchError,
    DomainError,
    DuplicateOrderLineError,
    DuplicateReservationError,
    GiftPriceError,
    InsufficientAvailableStockError,
    InsufficientPhysicalStockError,
    InvalidValueError,
    OrderCannotBePlacedError,
    OrderLineNotFoundError,
    OrderStateError,
    PaidLinePriceError,
    ReservationNotFoundError,
    ReservationStateError,
    SellerMismatchError,
)
from .identifiers import (
    BuyerId,
    Identifier,
    OrderId,
    OrderLineId,
    ReservationId,
    SellerId,
    StockItemId,
    WarehouseId,
)
from .order import Order, OrderLine, OrderLineSnapshot
from .stock_item import ReservationSummary, StockItem, StockReservation
from .values import (
    Currency,
    LineKind,
    Money,
    OrderStatus,
    Quantity,
    ReservationDeadline,
    ReservationStatus,
    ShippingAddress,
    Sku,
    StockBalance,
)

__all__ = [
    "BuyerId", "Currency", "CurrencyMismatchError", "DomainError",
    "DuplicateOrderLineError", "DuplicateReservationError", "GiftPriceError",
    "Identifier", "InsufficientAvailableStockError", "InsufficientPhysicalStockError",
    "InvalidValueError", "LineKind", "Money", "Order", "OrderCannotBePlacedError",
    "OrderId", "OrderLine", "OrderLineId", "OrderLineNotFoundError",
    "OrderLineSnapshot", "OrderStateError", "OrderStatus", "PaidLinePriceError",
    "Quantity", "ReservationDeadline", "ReservationId", "ReservationNotFoundError",
    "ReservationStateError", "ReservationStatus", "ReservationSummary",
    "SellerId", "SellerMismatchError", "ShippingAddress", "Sku",
    "StockBalance", "StockItem", "StockItemId", "StockReservation",
    "WarehouseId",
]