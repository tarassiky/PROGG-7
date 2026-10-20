from ..domain.payment import Payment
from ..domain.shipping import Shipment
from ..domain.inventory import StockItem, InsufficientStockError


class FulfillmentProcess:
    """
    Process Manager.
    Хранит состояние процесса и слушает факты.
    """

    def __init__(self, event_bus, order_repo):
        self.bus = event_bus
        self.order_repo = order_repo
        self.payment = None
        self.shipments = []
        self.reserved_items = []  # Список успешно зарезервированных позиций
        self.stock_db = {}  # Имитация базы склада

    def handle_order_placed(self, payload: dict):
        order_id = payload["order_id"]
        amount = payload["amount"]

        # 1. Авторизуем платеж
        self.payment = Payment(order_id, amount)
        self.payment.authorize()
        self.bus.publish("PaymentAuthorized", {"order_id": order_id})

        # 2. Резервируем склад
        for line in payload["lines"]:
            sku, qty = line["sku"], line["qty"]
            if sku not in self.stock_db:
                self.stock_db[sku] = StockItem(sku, balance=10)
            try:
                self.stock_db[sku].reserve(qty)
                self.reserved_items.append({"sku": sku, "qty": qty})
                self.bus.publish("InventoryReserved", {"order_id": order_id, "sku": sku})
            except InsufficientStockError:
                # КОМПЕНСАЦИЯ: не хватило остатка!
                self._compensate(order_id)
                return

        # 3. Создаем доставку
        shipment = Shipment(order_id)
        self.shipments.append(shipment)
        self.bus.publish("ShipmentCreated", {"order_id": order_id})

    def _compensate(self, order_id: str):
        # Откатываем то, что успели сделать
        for item in self.reserved_items:
            self.stock_db[item["sku"]]._balance += item["qty"]
        self.payment.void()

        # Переводим заказ в отказ
        order = self.order_repo.get(order_id)
        order.reject()
        self.bus.publish("OrderRejected", {"order_id": order_id})