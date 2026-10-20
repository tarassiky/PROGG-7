from decimal import Decimal
from .domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from .domain.order import Order
from .domain.catalog import CatalogItem
from .domain.inventory import StockItem
from .infrastructure.repositories import InMemoryOrderRepository


def run_demo():
    # 1. Каталог
    item = CatalogItem("BOOK-1", Decimal("1500.00"), "RUB")

    # 2. Оформление
    repo = InMemoryOrderRepository()
    order = Order(OrderId("ORD-2"), item.currency)
    order.add_line(Sku(item.sku), Money(item.price, item.currency), Quantity(2))
    order.set_address(ShippingAddress("СПБ", "Невский 1"))
    order.place()
    repo.save(order)

    # 3. Склад
    stock = StockItem("BOOK-1", balance=5)
    stock.reserve(2)

    return f"Заказ {order.id().value} оформлен. Остаток: {stock._balance}"