import unittest

from north_marketplace.domain import (
    InsufficientPhysicalStockError, Quantity, Sku, StockBalance, StockItem, StockItemId, WarehouseId
)


class StockBaselineTests(unittest.TestCase):
    def test_physical_balance_never_becomes_negative(self) -> None:
        stock = StockItem(StockItemId("ST-1"), WarehouseId("W-1"), Sku("BOOK-1"), StockBalance(10))

        stock.receive(Quantity(5))
        self.assertEqual(15, stock.physical_balance().amount())

        stock.write_off(Quantity(3))
        self.assertEqual(12, stock.physical_balance().amount())

        # Негатив: списание больше остатка
        with self.assertRaises(InsufficientPhysicalStockError):
            stock.write_off(Quantity(20))

        self.assertEqual(12, stock.physical_balance().amount())