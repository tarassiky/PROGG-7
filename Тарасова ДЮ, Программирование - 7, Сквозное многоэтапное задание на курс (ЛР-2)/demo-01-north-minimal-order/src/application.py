from decimal import Decimal
from .domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from .domain.order import Order

def run_demo():
    order = Order(OrderId("ORD-1"), "RUB")
    order.add_line(Sku("BOOK-1"), Money(Decimal("1000"), "RUB"), Quantity(2))
    order.set_address(ShippingAddress("Москва", "Тверская 1"))
    order.place()
    return f"Заказ {order.id().value} размещён. Сумма: {order.total().amount} {order.total().currency}"