import pytest
from decimal import Decimal
from src.domain.order import Order
from src.domain.values import OrderId, Money, Quantity, Sku, ShippingAddress, OrderStatus
from src.domain.errors import OrderCannotBePlacedError, CurrencyMismatchError

def test_place_order():
    order = Order(OrderId("1"), "RUB")
    order.add_line(Sku("B1"), Money(Decimal("100"), "RUB"), Quantity(1))
    order.set_address(ShippingAddress("M", "S"))
    order.place()
    assert order.status() == OrderStatus.PLACED

def test_no_address():
    order = Order(OrderId("1"), "RUB")
    order.add_line(Sku("B1"), Money(Decimal("100"), "RUB"), Quantity(1))
    with pytest.raises(OrderCannotBePlacedError):
        order.place()

def test_currency_mismatch():
    order = Order(OrderId("1"), "RUB")
    with pytest.raises(CurrencyMismatchError):
        order.add_line(Sku("B1"), Money(Decimal("100"), "USD"), Quantity(1))