from decimal import Decimal
from src.domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from src.domain.order import Order
from src.infrastructure.repositories import InMemoryOrderRepository
from src.infrastructure.event_bus import InMemoryEventBus
from src.process.fulfillment import FulfillmentProcess


def run_demo():
    bus = InMemoryEventBus()
    repo = InMemoryOrderRepository()
    process = FulfillmentProcess(bus, repo)
    bus.subscribe("OrderPlaced", process.handle_order_placed)

    # --- Успешный сценарий ---
    order = Order(OrderId("ORD-OK"), "RUB")
    order.add_line(Sku("BOOK-1"), Money(Decimal("1000"), "RUB"), Quantity(2))
    order.set_address(ShippingAddress("M", "S"))
    order.place()
    repo.save(order)

    bus.publish("OrderPlaced", {
        "order_id": order.id().value,
        "amount": float(order.total().amount),
        "lines": [{"sku": "BOOK-1", "qty": 2}]
    })

    # --- Неуспешный сценарий (не хватит остатка) ---
    order_fail = Order(OrderId("ORD-FAIL"), "RUB")
    order_fail.add_line(Sku("BOOK-X"), Money(Decimal("500"), "RUB"), Quantity(20))  # Склад даст только 10
    order_fail.set_address(ShippingAddress("M", "S"))
    order_fail.place()
    repo.save(order_fail)

    bus.publish("OrderPlaced", {
        "order_id": order_fail.id().value,
        "amount": float(order_fail.total().amount),
        "lines": [{"sku": "BOOK-X", "qty": 20}]
    })

    return f"Успех: {order.status().value}, Отказ: {order_fail.status().value}"