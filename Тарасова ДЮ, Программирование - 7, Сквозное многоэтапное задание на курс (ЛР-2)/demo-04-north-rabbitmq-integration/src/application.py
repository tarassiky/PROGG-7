from decimal import Decimal
from src.domain.values import OrderId, Money, Quantity, Sku, ShippingAddress
from src.domain.order import Order
from src.infrastructure.repositories import InMemoryOrderRepository
from src.infrastructure.outbox import Outbox
from src.infrastructure.inbox import Inbox
from src.process.fulfillment import FulfillmentProcess


class FakeRabbitMQ:
    """Имитация брокера для локального теста."""

    def __init__(self):
        self.queue = []

    def publish(self, event_type: str, payload: dict, msg_id: str):
        self.queue.append({"id": msg_id, "type": event_type, "payload": payload})


def outbox_relay(outbox: Outbox, broker: FakeRabbitMQ):
    """Relay: вычитывает Outbox и отправляет в брокер."""
    for msg in outbox.get_pending():
        broker.publish(msg.event_type, msg.payload, msg.id)
        outbox.mark_published(msg)


def consumer_loop(broker: FakeRabbitMQ, process: FulfillmentProcess, inbox: Inbox, outbox: Outbox):
    """Consumer: вычитывает из брокера, проверяет Inbox."""
    while broker.queue:
        msg = broker.queue.pop(0)

        # Защита от повторной доставки
        if inbox.is_processed(msg["id"]):
            continue

        if msg["type"] == "OrderPlaced":
            process.handle_order_placed(msg["payload"], outbox)
            inbox.mark_processed(msg["id"])


def run_demo():
    repo = InMemoryOrderRepository()
    outbox = Outbox()
    inbox = Inbox()
    broker = FakeRabbitMQ()
    process = FulfillmentProcess(broker, repo)

    # 1. Пользователь создаёт заказ
    order = Order(OrderId("ORD-1"), "RUB")
    order.add_line(Sku("BOOK-1"), Money(Decimal("1000"), "RUB"), Quantity(1))
    order.set_address(ShippingAddress("M", "S"))
    order.place()
    repo.save(order)

    # 2. Атомарно с сохранением добавляем в Outbox
    outbox.add("OrderPlaced", {
        "order_id": "ORD-1",
        "amount": 1000.0,
        "lines": [{"sku": "BOOK-1", "qty": 1}]
    })

    # 3. Relay отправляет в RabbitMQ
    outbox_relay(outbox, broker)

    # 4. Consumer обрабатывает
    consumer_loop(broker, process, inbox, outbox)

    # 5. Relay ещё раз (Process Manager мог создать новые события: PaymentAuthorized и т.д.)
    outbox_relay(outbox, broker)

    return f"Заказ {order.id().value} обработан. Статус платежа: {process.payment.status}. Отправлено сообщений: {len(broker.queue)}"