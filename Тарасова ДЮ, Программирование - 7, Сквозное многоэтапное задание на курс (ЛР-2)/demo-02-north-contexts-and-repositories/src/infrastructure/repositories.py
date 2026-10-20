from src.domain.order import Order

class InMemoryOrderRepository:
    def __init__(self):
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.id().value] = order

    def get(self, order_id: str) -> Order:
        return self._orders[order_id]