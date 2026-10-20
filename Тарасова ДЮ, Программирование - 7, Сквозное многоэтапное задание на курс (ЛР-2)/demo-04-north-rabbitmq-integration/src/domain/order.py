from dataclasses import dataclass
from decimal import Decimal
from .values import OrderId, Money, Quantity, Sku, ShippingAddress, OrderStatus
from .errors import CurrencyMismatchError, OrderCannotBePlacedError, OrderStateError

@dataclass
class OrderLine:
    sku: Sku
    unit_price: Money
    quantity: Quantity
    def subtotal(self) -> Money:
        return Money(self.unit_price.amount * self.quantity.value, self.unit_price.currency)

class Order:
    def __init__(self, order_id: OrderId, currency: str):
        self._id = order_id
        self._currency = currency
        self._status = OrderStatus.DRAFT
        self._lines: list[OrderLine] = []
        self._address: ShippingAddress | None = None

    def id(self) -> OrderId: return self._id
    def status(self) -> OrderStatus: return self._status
    def lines(self) -> tuple[OrderLine, ...]: return tuple(self._lines)

    def add_line(self, sku: Sku, price: Money, qty: Quantity) -> None:
        if self._status != OrderStatus.DRAFT:
            raise OrderStateError("Менять можно только черновик")
        if price.currency != self._currency:
            raise CurrencyMismatchError("Валюта не совпадает")
        self._lines.append(OrderLine(sku, price, qty))

    def set_address(self, address: ShippingAddress) -> None:
        if self._status != OrderStatus.DRAFT:
            raise OrderStateError("Менять можно только черновик")
        self._address = address

    def total(self) -> Money:
        total = Decimal("0")
        for line in self._lines:
            total += line.subtotal().amount
        return Money(total, self._currency)

    def place(self) -> None:
        if self._status != OrderStatus.DRAFT:
            raise OrderStateError("Заказ уже размещён")
        if not self._lines: raise OrderCannotBePlacedError("Пустой заказ")
        if not self._address: raise OrderCannotBePlacedError("Нет адреса")
        if self.total().amount <= 0: raise OrderCannotBePlacedError("Сумма <= 0")
        self._status = OrderStatus.PLACED

    def reject(self) -> None:
        if self._status == OrderStatus.PLACED:
            self._status = OrderStatus.REJECTED