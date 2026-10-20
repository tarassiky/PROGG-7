import unittest
from decimal import Decimal

from north_marketplace.domain import (
    BuyerId, Currency, DuplicateOrderLineError, Money, Order, OrderId,
    OrderLineId, Quantity, SellerId, SellerMismatchError, Sku,
)


class OrderSellerTests(unittest.TestCase):
    def test_line_id_is_unique_and_first_seller_rejects_another_seller(self) -> None:
        order = Order(OrderId("O-2"), BuyerId("B-2"), Currency("RUB"))
        seller_a = SellerId("SELLER-A")

        order.add_paid_line(OrderLineId("L-1"), Sku("BOOK-1"), "Книга", seller_a,
                            Money(Decimal("100"), Currency("RUB")), Quantity(1))

        # Негатив 1: повторный OrderLineId
        with self.assertRaises(DuplicateOrderLineError):
            order.add_paid_line(OrderLineId("L-1"), Sku("BOOK-2"), "Другая", seller_a,
                                Money(Decimal("200"), Currency("RUB")), Quantity(1))

        # Негатив 2: второй продавец
        with self.assertRaises(SellerMismatchError):
            order.add_paid_line(OrderLineId("L-2"), Sku("BOOK-3"), "Третья", SellerId("SELLER-B"),
                                Money(Decimal("300"), Currency("RUB")), Quantity(1))

        self.assertEqual(1, len(order.lines()))
        self.assertEqual(seller_a, order.seller_id())