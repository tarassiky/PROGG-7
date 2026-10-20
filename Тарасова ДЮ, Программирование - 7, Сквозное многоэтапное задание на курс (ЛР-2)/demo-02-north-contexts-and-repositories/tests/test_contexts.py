import pytest
from decimal import Decimal
from src.domain.order import Order
from src.domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from src.domain.inventory import StockItem, InsufficientStockError
from src.infrastructure.repositories import InMemoryOrderRepository

def test_repository_saves_order():
    repo = InMemoryOrderRepository()
    order = Order(OrderId("1"), "RUB")
    repo.save(order)
    assert repo.get("1").id().value == "1"

def test_stock_reserves():
    stock = StockItem("B1", 5)
    stock.reserve(2)
    assert stock._balance == 3

def test_stock_fails():
    stock = StockItem("B1", 5)
    with pytest.raises(InsufficientStockError):
        stock.reserve(10)