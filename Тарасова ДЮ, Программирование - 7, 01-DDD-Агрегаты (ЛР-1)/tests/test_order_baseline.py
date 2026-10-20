import unittest
from decimal import Decimal

from north_marketplace.domain import (
    BuyerId,
    Currency,
    CurrencyMismatchError,
    Money,
    Order,
    OrderCannotBePlacedError,
    OrderId,
    OrderLineId,
    OrderLineNotFoundError,
    OrderStatus,
    Quantity,
    SellerId,
    ShippingAddress,
    Sku,
)


def rub() -> Currency:
    return Currency("RUB")


def make_seller() -> SellerId:
    return SellerId("SELLER-1")


def make_order() -> Order:
    return Order(OrderId("ORD-1"), BuyerId("BUYER-1"), rub())


def full_order() -> Order:
    order = make_order()
    order.add_paid_line(
        OrderLineId("L-1"),
        Sku("BOOK-1"),
        "Книга",
        make_seller(),
        Money(Decimal("1000.00"), rub()),
        Quantity(1),
    )
    order.set_shipping_address(
        ShippingAddress("Архангельск", "Поморская", "18", "163000")
    )
    return order


class OrderBaselineTests(unittest.TestCase):
    def test_rejects_different_currency_without_adding_line(self) -> None:
        order = make_order()
        with self.assertRaises(CurrencyMismatchError):
            order.add_paid_line(
                OrderLineId("L-1"), Sku("BOOK-1"), "Книга", make_seller(),
                Money(Decimal("10.00"), Currency("USD")), Quantity(1),
            )
        self.assertEqual(0, len(order.lines()))

    def test_change_quantity_by_id(self) -> None:
        order = full_order()
        order.change_line_quantity(OrderLineId("L-1"), Quantity(3))
        self.assertEqual(Decimal("3000.00"), order.total().amount())

    def test_unknown_line_id_is_rejected(self) -> None:
        order = full_order()
        with self.assertRaises(OrderLineNotFoundError):
            order.change_line_quantity(OrderLineId("MISSING"), Quantity(2))

    def test_empty_order_cannot_be_placed(self) -> None:
        with self.assertRaises(OrderCannotBePlacedError):
            make_order().place()

    def test_order_without_address_cannot_be_placed(self) -> None:
        order = make_order()
        order.add_paid_line(
            OrderLineId("L-1"), Sku("BOOK-1"), "Книга", make_seller(),
            Money(Decimal("100"), rub()), Quantity(1),
        )
        with self.assertRaises(OrderCannotBePlacedError):
            order.place()
        self.assertEqual(OrderStatus.DRAFT, order.status())

    def test_place_requires_full_order(self) -> None:
        order = full_order()
        order.place()
        self.assertEqual(OrderStatus.PLACED, order.status())
        self.assertEqual(Decimal("1000.00"), order.total().amount())

    def test_placed_order_is_immutable(self) -> None:
        order = full_order()
        order.place()
        with self.assertRaises(Exception):  # OrderStateError
            order.add_paid_line(
                OrderLineId("L-2"), Sku("BOOK-2"), "Другая", make_seller(),
                Money(Decimal("100"), rub()), Quantity(1),
            )