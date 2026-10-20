from src.domain.payment import Payment
from src.domain.shipping import Shipment
from src.domain.inventory import StockItem, InsufficientStockError
from src.infrastructure.outbox import Outbox


class FulfillmentProcess:
    """Process Manager с поддержкой Outbox."""

    def __init__(self, publisher, order_repo):
        self.publisher = publisher
        self.order_repo = order_repo
        self.payment = None
        self.shipments = []
        self.reserved_items = []
        self.stock_db = {}

    def handle_order_placed(self, payload: dict, outbox: Outbox):
        order_id = payload["order_id"]
        amount = payload["amount"]

        # 1. Платёж
        self.payment = Payment(order_id, amount)
        self.payment.authorize()
        outbox.add("PaymentAuthorized", {"order_id": order_id})

        # 2. Склад
        for line in payload["lines"]:
            sku, qty = line["sku"], line["qty"]
            if sku not in self.stock_db:
                self.stock_db[sku] = StockItem(sku, balance=10)
            try:
                self.stock_db[sku].reserve(qty)
                self.reserved_items.append({"sku": sku, "qty": qty})
                outbox.add("InventoryReserved", {"order_id": order_id, "sku": sku})
            except InsufficientStockError:
                self._compensate(order_id, outbox)
                return

        # 3. Доставка
        shipment = Shipment(order_id)
        self.shipments.append(shipment)
        outbox.add("ShipmentCreated", {"order_id": order_id})

    def _compensate(self, order_id: str, outbox: Outbox):
        for item in self.reserved_items:
            self.stock_db[item["sku"]].release(item["qty"])
        self.payment.void()

        order = self.order_repo.get(order_id)
        order.reject()
        outbox.add("OrderRejected", {"order_id": order_id})