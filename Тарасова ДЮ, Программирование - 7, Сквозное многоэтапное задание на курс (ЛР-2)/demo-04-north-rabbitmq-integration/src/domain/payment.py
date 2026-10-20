from .errors import PaymentStateError

class Payment:
    def __init__(self, order_id: str, amount: float):
        self.order_id = order_id
        self.amount = amount
        self.status = "PENDING"

    def authorize(self) -> None:
        if self.status != "PENDING": raise PaymentStateError("Уже авторизован")
        self.status = "AUTHORIZED"

    def void(self) -> None:
        if self.status != "AUTHORIZED": raise PaymentStateError("Нечего отменять")
        self.status = "VOIDED"