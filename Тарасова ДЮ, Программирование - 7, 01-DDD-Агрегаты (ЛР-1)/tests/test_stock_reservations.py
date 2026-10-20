import unittest
from datetime import datetime, timedelta, timezone

from north_marketplace.domain import (
    InsufficientAvailableStockError, OrderId, Quantity, ReservationDeadline,
    ReservationId, ReservationStatus, Sku, StockBalance, StockItem, StockItemId, WarehouseId
)


class StockReservationTests(unittest.TestCase):
    def test_active_reservations_do_not_exceed_available_balance(self) -> None:
        stock = StockItem(StockItemId("ST-2"), WarehouseId("W-2"), Sku("BOOK-1"), StockBalance(10))
        deadline = ReservationDeadline(datetime.now(timezone.utc) + timedelta(hours=1))

        stock.reserve(ReservationId("R-1"), OrderId("O-1"), Quantity(4), deadline)
        self.assertEqual(6, stock.available_quantity())

        # Негатив: превышение доступного
        with self.assertRaises(InsufficientAvailableStockError):
            stock.reserve(ReservationId("R-2"), OrderId("O-2"), Quantity(7), deadline)

        self.assertEqual(1, len(stock.reservations()))

        # Освобождение не удаляет резерв
        stock.release_reservation(ReservationId("R-1"))
        self.assertEqual(1, len(stock.reservations()))
        self.assertEqual(ReservationStatus.RELEASED, stock.reservations()[0].status)
        self.assertEqual(10, stock.available_quantity())