from .errors import DomainError

class InsufficientStockError(DomainError): pass

class StockItem:
    def __init__(self, sku: str, balance: int):
        self.sku = sku
        self._balance = balance

    def reserve(self, qty: int) -> None:
        if qty > self._balance:
            raise InsufficientStockError(f"Не хватает {self.sku}")
        self._balance -= qty

    def release(self, qty: int) -> None:
        self._balance += qty