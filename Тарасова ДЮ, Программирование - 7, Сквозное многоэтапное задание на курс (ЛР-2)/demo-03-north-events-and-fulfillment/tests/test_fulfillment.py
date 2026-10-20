from decimal import Decimal
from src.domain.order import Order
from src.domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from src.infrastructure.repositories import InMemoryOrderRepository
from src.infrastructure.event_bus import InMemoryEventBus
from src.process.fulfillment import FulfillmentProcess


def test_fulfillment_success():
    bus = InMemoryEventBus()
    repo = InMemoryOrderRepository()
    process = FulfillmentProcess(bus, repo)
    bus.subscribe("OrderPlaced", process.handle_order_placed)

    order = Order(OrderId("O-1"), "RUB")
    order.add_line(Sku("B1"), Money(Decimal("100"), "RUB"), Quantity(1))
    order.set_address(ShippingAddress("M", "S"))
    order.place()
    repo.save(order)

    bus.publish("OrderPlaced", {
        "order_id": "O-1", "amount": 100.0, "lines": [{"sku": "B1", "qty": 1}]
    })

    assert process.payment.status == "AUTHORIZED"
    assert len(process.shipments) == 1


def test_fulfillment_fails_and_compensates():
    bus = InMemoryEventBus()
    repo = InMemoryOrderRepository()
    process = FulfillmentProcess(bus, repo)
    bus.subscribe("OrderPlaced", process.handle_order_placed)

    order = Order(OrderId("O-2"), "RUB")
    order.add_line(Sku("B1"), Money(Decimal("100"), "RUB"), Quantity(100))
    order.set_address(ShippingAddress("M", "S"))
    order.place()
    repo.save(order)

    bus.publish("OrderPlaced", {
        "order_id": "O-2", "amount": 10000.0, "lines": [{"sku": "B1", "qty": 100}]
    })

    assert process.payment.status == "VOIDED"
    assert len(process.shipments) == 0