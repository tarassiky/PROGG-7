"""Агрегат заказа."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .errors import (
    CurrencyMismatchError,
    DuplicateOrderLineError,
    GiftPriceError,
    OrderCannotBePlacedError,
    OrderLineNotFoundError,
    OrderStateError,
    PaidLinePriceError,
    SellerMismatchError,
)
from .identifiers import BuyerId, OrderId, OrderLineId, SellerId
from .values import (
    Currency,
    LineKind,
    Money,
    OrderStatus,
    Quantity,
    ShippingAddress,
    Sku,
)


@dataclass(frozen=True)
class OrderLineSnapshot:
    """Неизменяемый снимок строки заказа для чтения."""

    line_id: OrderLineId
    sku: Sku
    title: str
    seller_id: SellerId
    unit_price: Money
    quantity: Quantity
    kind: LineKind

    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)


class OrderLine:
    """Внутренняя сущность заказа; создаётся и изменяется только Order."""

    def __init__(
        self,
        line_id: OrderLineId,
        sku: Sku,
        title: str,
        seller_id: SellerId,
        unit_price: Money,
        quantity: Quantity,
        kind: LineKind,
    ) -> None:
        if not isinstance(line_id, OrderLineId):
            raise OrderStateError("OrderLine требует OrderLineId")
        if not isinstance(title, str) or not title.strip():
            raise OrderStateError("Наименование строки не может быть пустым")
        if kind is LineKind.GIFT and unit_price.amount() != Decimal("0"):
            raise GiftPriceError("Подарочная строка должна иметь нулевую цену")
        if kind is LineKind.PAID and unit_price.amount() <= Decimal("0"):
            raise PaidLinePriceError("Платная строка должна иметь положительную цену")
        self._id = line_id
        self._sku = sku
        self._title = title.strip()
        self._seller_id = seller_id
        self._unit_price = unit_price
        self._quantity = quantity
        self._kind = kind

    def id(self) -> OrderLineId:
        return self._id

    def seller_id(self) -> SellerId:
        return self._seller_id

    def unit_price(self) -> Money:
        return self._unit_price

    def kind(self) -> LineKind:
        return self._kind

    def subtotal(self) -> Money:
        return self._unit_price.multiply(self._quantity)

    def _change_quantity(self, quantity: Quantity) -> None:
        self._quantity = quantity

    def _snapshot(self) -> OrderLineSnapshot:
        return OrderLineSnapshot(
            line_id=self._id,
            sku=self._sku,
            title=self._title,
            seller_id=self._seller_id,
            unit_price=self._unit_price,
            quantity=self._quantity,
            kind=self._kind,
        )


class Order:
    """Корень агрегата заказа."""

    def __init__(self, order_id: OrderId, buyer_id: BuyerId, currency: Currency) -> None:
        if not isinstance(order_id, OrderId):
            raise OrderStateError("Order требует OrderId")
        if not isinstance(buyer_id, BuyerId):
            raise OrderStateError("Order требует BuyerId")
        if not isinstance(currency, Currency):
            raise OrderStateError("Order требует Currency")
        self._id = order_id
        self._buyer_id = buyer_id
        self._currency = currency
        self._status = OrderStatus.DRAFT
        self._seller_id: SellerId | None = None
        self._lines: list[OrderLine] = []
        self._shipping_address: ShippingAddress | None = None

    # --- запросы -----------------------------------------------------------

    def id(self) -> OrderId:
        return self._id

    def buyer_id(self) -> BuyerId:
        return self._buyer_id

    def currency(self) -> Currency:
        return self._currency

    def status(self) -> OrderStatus:
        return self._status

    def seller_id(self) -> SellerId | None:
        return self._seller_id

    def shipping_address(self) -> ShippingAddress | None:
        return self._shipping_address

    def lines(self) -> tuple[OrderLineSnapshot, ...]:
        return tuple(line._snapshot() for line in self._lines)

    def total(self) -> Money:
        total = Money(Decimal("0"), self._currency)
        for line in self._lines:
            total = total.add(line.subtotal())
        return total

    # --- команды -----------------------------------------------------------

    def add_paid_line(
        self,
        line_id: OrderLineId,
        sku: Sku,
        title: str,
        seller_id: SellerId,
        price: Money,
        quantity: Quantity,
    ) -> None:
        self._require_draft()
        if price.currency() != self._currency:
            raise CurrencyMismatchError(
                "Валюта строки должна совпадать с валютой заказа"
            )
        line = OrderLine(line_id, sku, title, seller_id, price, quantity, LineKind.PAID)
        self._attach_line(line)

    def add_gift_line(
        self,
        line_id: OrderLineId,
        sku: Sku,
        title: str,
        seller_id: SellerId,
        quantity: Quantity,
    ) -> None:
        self._require_draft()
        zero_price = Money(Decimal("0"), self._currency)
        line = OrderLine(line_id, sku, title, seller_id, zero_price, quantity, LineKind.GIFT)
        self._attach_line(line)

    def change_line_quantity(self, line_id: OrderLineId, quantity: Quantity) -> None:
        self._require_draft()
        line = self._find_line(line_id)
        line._change_quantity(quantity)

    def set_shipping_address(self, address: ShippingAddress) -> None:
        self._require_draft()
        if not isinstance(address, ShippingAddress):
            raise OrderStateError("Order требует ShippingAddress")
        self._shipping_address = address

    def place(self) -> None:
        self._require_draft()
        if not self._lines:
            raise OrderCannotBePlacedError("Нельзя разместить пустой заказ")
        if self._shipping_address is None:
            raise OrderCannotBePlacedError("Нельзя разместить заказ без адреса")
        if not any(line.kind() is LineKind.PAID for line in self._lines):
            raise OrderCannotBePlacedError(
                "Заказ должен содержать хотя бы одну платную строку"
            )
        if self.total().amount() <= Decimal("0"):
            raise OrderCannotBePlacedError("Итог заказа должен быть положительным")
        self._status = OrderStatus.PLACED

    def cancel(self) -> None:
        if self._status is OrderStatus.CANCELLED:
            raise OrderStateError("Отменённый заказ нельзя отменить повторно")
        self._status = OrderStatus.CANCELLED

    # --- внутренние помощники ---------------------------------------------

    def _attach_line(self, line: OrderLine) -> None:
        if any(existing.id() == line.id() for existing in self._lines):
            raise DuplicateOrderLineError(
                f"OrderLineId {line.id().value()!r} уже существует"
            )
        if self._seller_id is not None and self._seller_id != line.seller_id():
            raise SellerMismatchError("Все строки заказа должны быть от одного продавца")
        if self._seller_id is None:
            self._seller_id = line.seller_id()
        self._lines.append(line)

    def _find_line(self, line_id: OrderLineId) -> OrderLine:
        for line in self._lines:
            if line.id() == line_id:
                return line
        raise OrderLineNotFoundError(
            f"Строка {line_id.value()!r} не найдена в заказе"
        )

    def _require_draft(self) -> None:
        if self._status is not OrderStatus.DRAFT:
            raise OrderStateError("Изменять можно только черновик заказа")