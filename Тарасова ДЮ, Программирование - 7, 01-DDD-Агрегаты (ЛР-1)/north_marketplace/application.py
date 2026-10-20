"""Детерминированный прикладной сценарий: два корня, явные вызовы."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .domain import (
    BuyerId,
    Currency,
    Money,
    Order,
    OrderId,
    OrderLineId,
    Quantity,
    ReservationDeadline,
    ReservationId,
    SellerId,
    ShippingAddress,
    Sku,
    StockBalance,
    StockItem,
    StockItemId,
    WarehouseId,
)


def run_demo() -> str:
    rub = Currency("RUB")
    order = Order(OrderId("order-100"), BuyerId("buyer-20"), rub)
    seller_id = SellerId("seller-7")

    order.add_paid_line(
        OrderLineId("line-1"),
        Sku("BOOK-001"),
        "Книга о Севере",
        seller_id,
        Money(Decimal("1290.00"), rub),
        Quantity(1),
    )
    order.add_gift_line(
        OrderLineId("line-2"),
        Sku("BOOKMARK-001"),
        "Закладка",
        seller_id,
        Quantity(1),
    )
    order.set_shipping_address(
        ShippingAddress("Архангельск", "Поморская", "18", "163000")
    )
    order.place()

    stock_item = StockItem(
        StockItemId("stock-400"),
        WarehouseId("warehouse-ark"),
        Sku("BOOK-001"),
        StockBalance(8),
    )
    deadline = ReservationDeadline(
        datetime.now(timezone.utc) + timedelta(hours=1)
    )
    stock_item.reserve(
        ReservationId("reservation-900"),
        order.id(),
        Quantity(1),
        deadline,
    )

    return (
        f"Заказ {order.id().value()}: {order.status().value}, "
        f"сумма {order.total().amount()} {order.total().currency().code()}\n"
        f"Физический остаток: {stock_item.physical_balance().amount()}\n"
        f"Доступный остаток: {stock_item.available_quantity()}\n"
        f"Создан резерв по OrderId {order.id().value()}"
    )


def main() -> int:
    print(run_demo())
    return 0