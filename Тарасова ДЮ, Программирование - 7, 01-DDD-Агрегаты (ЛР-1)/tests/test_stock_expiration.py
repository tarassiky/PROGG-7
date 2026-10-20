import unittest
from datetime import datetime, timedelta, timezone

from north_marketplace.domain import (
    OrderId, Quantity, ReservationDeadline, ReservationId, ReservationStatus,
    Sku, StockBalance, StockItem, StockItemId, WarehouseId
)


class StockExpirationTests(unittest.TestCase):
    def test_due_reservation_expires_and_releases_balance(self) -> None:
        stock = StockItem(StockItemId("ST-3"), WarehouseId("W-3"), Sku("BOOK-1"), StockBalance(5))
        now = datetime.now(timezone.utc)

        # Просроченный
        stock.reserve(ReservationId("R-1"), OrderId("O-1"), Quantity(2), ReservationDeadline(now - timedelta(hours=1)))
        # Будущий
        stock.reserve(ReservationId("R-2"), OrderId("O-2"), Quantity(2), ReservationDeadline(now + timedelta(hours=1)))

        self.assertEqual(1, stock.available_quantity())

        expired = stock.expire_reservations(now)
        self.assertEqual(1, expired)

        self.assertEqual(ReservationStatus.EXPIRED, stock.reservations()[0].status)
        self.assertEqual(ReservationStatus.ACTIVE, stock.reservations()[1].status)
        self.assertEqual(3, stock.available_quantity())