"""Объекты-значения и перечисления."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

from .errors import InvalidValueError


class Currency:
    """Трёхбуквенный код валюты в верхнем регистре."""

    def __init__(self, code: str) -> None:
        if (
            not isinstance(code, str)
            or len(code.strip()) != 3
            or not code.strip().isalpha()
        ):
            raise InvalidValueError("Код валюты состоит из трёх букв")
        self._code = code.strip().upper()

    def code(self) -> str:
        return self._code

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Currency) and self._code == other._code

    def __hash__(self) -> int:
        return hash(("Currency", self._code))

    def __repr__(self) -> str:
        return f"Currency({self._code!r})"


class Sku:
    def __init__(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidValueError("Sku должен быть непустой строкой")
        self._value = value.strip().upper()

    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sku) and self._value == other._value

    def __hash__(self) -> int:
        return hash(("Sku", self._value))

    def __repr__(self) -> str:
        return f"Sku({self._value!r})"


class Quantity:
    """Положительное целое количество."""

    def __init__(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise InvalidValueError("Количество должно быть положительным целым")
        self._value = value

    def value(self) -> int:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Quantity) and self._value == other._value

    def __hash__(self) -> int:
        return hash(("Quantity", self._value))

    def __repr__(self) -> str:
        return f"Quantity({self._value})"


class Money:
    """Неотрицательная Decimal-сумма в валюте."""

    def __init__(self, amount: Decimal | str | int, currency: Currency) -> None:
        if not isinstance(currency, Currency):
            raise InvalidValueError("Money требует Currency")
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError) as error:
            raise InvalidValueError("Сумма Money должна быть Decimal") from error
        if not decimal_amount.is_finite() or decimal_amount < Decimal("0"):
            raise InvalidValueError("Сумма Money должна быть неотрицательной")
        self._amount = decimal_amount
        self._currency = currency

    def amount(self) -> Decimal:
        return self._amount

    def currency(self) -> Currency:
        return self._currency

    def add(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise InvalidValueError("Складывать можно только Money")
        if self._currency != other._currency:
            raise InvalidValueError("Складывать суммы разных валют нельзя")
        return Money(self._amount + other._amount, self._currency)

    def multiply(self, quantity: Quantity) -> "Money":
        if not isinstance(quantity, Quantity):
            raise InvalidValueError("Money умножается только на Quantity")
        return Money(self._amount * quantity.value(), self._currency)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Money)
            and self._amount == other._amount
            and self._currency == other._currency
        )

    def __hash__(self) -> int:
        return hash(("Money", self._amount, self._currency))

    def __repr__(self) -> str:
        return f"Money({self._amount}, {self._currency.code()!r})"


class ShippingAddress:
    def __init__(self, city: str, street: str, building: str, postal_code: str) -> None:
        parts = (city, street, building, postal_code)
        if any(not isinstance(p, str) or not p.strip() for p in parts):
            raise InvalidValueError("Все поля адреса должны быть непустыми")
        self._city = city.strip()
        self._street = street.strip()
        self._building = building.strip()
        self._postal_code = postal_code.strip()

    def city(self) -> str:
        return self._city

    def street(self) -> str:
        return self._street

    def building(self) -> str:
        return self._building

    def postal_code(self) -> str:
        return self._postal_code

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ShippingAddress)
            and (self._city, self._street, self._building, self._postal_code)
            == (other._city, other._street, other._building, other._postal_code)
        )

    def __hash__(self) -> int:
        return hash(("ShippingAddress", self._city, self._street,
                     self._building, self._postal_code))

    def __repr__(self) -> str:
        return (
            f"ShippingAddress({self._city!r}, {self._street!r}, "
            f"{self._building!r}, {self._postal_code!r})"
        )


class StockBalance:
    """Неотрицательное целое физическое количество."""

    def __init__(self, amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise InvalidValueError("StockBalance должен быть неотрицательным целым")
        self._amount = amount

    def amount(self) -> int:
        return self._amount

    def increase(self, quantity: Quantity) -> "StockBalance":
        if not isinstance(quantity, Quantity):
            raise InvalidValueError("StockBalance принимает Quantity")
        return StockBalance(self._amount + quantity.value())

    def decrease(self, quantity: Quantity) -> "StockBalance":
        if not isinstance(quantity, Quantity):
            raise InvalidValueError("StockBalance принимает Quantity")
        if quantity.value() > self._amount:
            from .errors import InsufficientPhysicalStockError
            raise InsufficientPhysicalStockError(
                "Нельзя списать больше физического остатка"
            )
        return StockBalance(self._amount - quantity.value())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StockBalance) and self._amount == other._amount

    def __hash__(self) -> int:
        return hash(("StockBalance", self._amount))

    def __repr__(self) -> str:
        return f"StockBalance({self._amount})"


class ReservationDeadline:
    """Момент времени с часовым поясом."""

    def __init__(self, moment: datetime) -> None:
        if (
            not isinstance(moment, datetime)
            or moment.tzinfo is None
            or moment.utcoffset() is None
        ):
            raise InvalidValueError(
                "ReservationDeadline требует datetime с часовым поясом"
            )
        self._moment = moment

    def moment(self) -> datetime:
        return self._moment

    def is_reached_at(self, now: datetime) -> bool:
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise InvalidValueError(
                "Текущий момент должен быть datetime с часовым поясом"
            )
        return now >= self._moment

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ReservationDeadline) and self._moment == other._moment

    def __hash__(self) -> int:
        return hash(("ReservationDeadline", self._moment))


class OrderStatus(Enum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"


class LineKind(Enum):
    PAID = "PAID"
    GIFT = "GIFT"


class ReservationStatus(Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"