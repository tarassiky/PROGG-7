import unittest
from decimal import Decimal

from north_marketplace.domain import (
    BuyerId, Currency, GiftPriceError, Money, Order, OrderCannotBePlacedError,
    OrderId, OrderLineId, OrderStateError, OrderStatus, Quantity, SellerId, ShippingAddress, Sku
)


class OrderGiftTests(unittest.TestCase):
    def test_gift_does_not_replace_a_paid_line_and_lines_are_snapshots(self) -> None:
        order = Order(OrderId("O-3"), BuyerId("B-3"), Currency("RUB"))
        seller = SellerId("S-1")

        # Негатив: подарок с ценой > 0
        with self.assertRaises(GiftPriceError):
            from north_marketplace.domain.order import OrderLine
            from north_marketplace.domain.values import LineKind
            OrderLine(OrderLineId("L-1"), Sku("K-1"), "Т", seller, Money(Decimal("1"), Currency("RUB")), Quantity(1),
                      LineKind.GIFT)

        # Заказ только с подарком нельзя разместить
        order.add_gift_line(OrderLineId("L-1"), Sku("K-1"), "Подарок", seller, Quantity(1))
        order.set_shipping_address(ShippingAddress("Город", "Улица", "1", "123456"))

        with self.assertRaises(OrderCannotBePlacedError):
            order.place()

        # Добавляем платную строку, теперь можно
        order.add_paid_line(OrderLineId("L-2"), Sku("K-2"), "Товар", seller, Money(Decimal("500"), Currency("RUB")),
                            Quantity(1))
        order.place()
        self.assertEqual(OrderStatus.PLACED, order.status())

        # Изменение после place запрещено
        with self.assertRaises(OrderStateError):
            order.add_gift_line(OrderLineId("L-3"), Sku("K-3"), "Ещё", seller, Quantity(1))