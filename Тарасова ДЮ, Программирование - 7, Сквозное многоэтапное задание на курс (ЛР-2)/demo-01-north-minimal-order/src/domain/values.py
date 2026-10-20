from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from .errors import InvalidValueError

@dataclass(frozen=True)
class OrderId:
    value: str
    def __post_init__(self):
        if not self.value.strip(): raise InvalidValueError("OrderId пуст")

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    def __post_init__(self):
        if self.amount < 0: raise InvalidValueError("Сумма < 0")
        if len(self.currency) != 3: raise InvalidValueError("Валюта должна быть 3 буквы")

@dataclass(frozen=True)
class Quantity:
    value: int
    def __post_init__(self):
        if self.value <= 0: raise InvalidValueError("Количество должно быть > 0")

@dataclass(frozen=True)
class Sku:
    value: str
    def __post_init__(self):
        if not self.value.strip(): raise InvalidValueError("Sku пуст")

@dataclass(frozen=True)
class ShippingAddress:
    city: str
    street: str

class OrderStatus(Enum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"