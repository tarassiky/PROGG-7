"""Типизированные идентификаторы."""

from __future__ import annotations

from .errors import InvalidValueError


class Identifier:
    """Базовый неизменяемый идентификатор с непустым строковым значением."""

    _label = "Идентификатор"

    def __init__(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidValueError(f"{self._label} должен быть непустой строкой")
        self._value = value.strip()

    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self._value == other._value  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._value))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value!r})"


class OrderId(Identifier):
    _label = "OrderId"


class OrderLineId(Identifier):
    _label = "OrderLineId"


class BuyerId(Identifier):
    _label = "BuyerId"


class SellerId(Identifier):
    _label = "SellerId"


class StockItemId(Identifier):
    _label = "StockItemId"


class WarehouseId(Identifier):
    _label = "WarehouseId"


class ReservationId(Identifier):
    _label = "ReservationId"