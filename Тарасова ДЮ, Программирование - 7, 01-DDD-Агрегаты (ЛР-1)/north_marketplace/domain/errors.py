"""Доменные ошибки."""


class DomainError(Exception):
    """Базовая доменная ошибка."""


class InvalidValueError(DomainError):
    """Недопустимое значение объекта-значения или идентификатора."""


class OrderStateError(DomainError):
    """Команда запрещена текущим состоянием заказа."""


class CurrencyMismatchError(DomainError):
    """Валюта строки не совпадает с валютой заказа."""


class SellerMismatchError(DomainError):
    """Строка относится к другому продавцу."""


class DuplicateOrderLineError(DomainError):
    """OrderLineId уже существует в заказе."""


class OrderLineNotFoundError(DomainError):
    """Строка заказа не найдена по OrderLineId."""


class GiftPriceError(DomainError):
    """Подарочная строка должна иметь нулевую цену."""


class PaidLinePriceError(DomainError):
    """Платная строка должна иметь положительную цену."""


class OrderCannotBePlacedError(DomainError):
    """Заказ неполон для размещения."""


class InsufficientPhysicalStockError(DomainError):
    """Списание больше физического остатка."""


class InsufficientAvailableStockError(DomainError):
    """Недостаточно доступного остатка."""


class DuplicateReservationError(DomainError):
    """ReservationId уже существует в складской позиции."""


class ReservationNotFoundError(DomainError):
    """Резерв не найден в складской позиции."""


class ReservationStateError(DomainError):
    """Переход запрещён текущим состоянием резерва."""