"""Агрегат складской позиции."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .errors import (
    DuplicateReservationError,
    InsufficientAvailableStockError,
    ReservationNotFoundError,
    ReservationStateError,
)
from .identifiers import OrderId, ReservationId, StockItemId, WarehouseId
from .values import (
    Quantity,
    ReservationDeadline,
    ReservationStatus,
    Sku,
    StockBalance,
)


@dataclass(frozen=True)
class ReservationSummary:
    """Неизменяемый снимок резерва для чтения."""

    reservation_id: ReservationId
    order_id: OrderId
    quantity: Quantity
    deadline: ReservationDeadline
    status: ReservationStatus


class StockReservation:
    """Внутренняя сущность StockItem."""

    def __init__(
        self,
        reservation_id: ReservationId,
        order_id: OrderId,
        quantity: Quantity,
        deadline: ReservationDeadline,
    ) -> None:
        if not isinstance(reservation_id, ReservationId):
            raise ReservationStateError("StockReservation требует ReservationId")
        if not isinstance(order_id, OrderId):
            raise ReservationStateError("StockReservation требует OrderId")
        if not isinstance(quantity, Quantity):
            raise ReservationStateError("StockReservation требует Quantity")
        if not isinstance(deadline, ReservationDeadline):
            raise ReservationStateError("StockReservation требует ReservationDeadline")
        self._id = reservation_id
        self._order_id = order_id
        self._quantity = quantity
        self._deadline = deadline
        self._status = ReservationStatus.ACTIVE

    def id(self) -> ReservationId:
        return self._id

    def order_id(self) -> OrderId:
        return self._order_id

    def quantity(self) -> Quantity:
        return self._quantity

    def deadline(self) -> ReservationDeadline:
        return self._deadline

    def status(self) -> ReservationStatus:
        return self._status

    def is_active(self) -> bool:
        return self._status is ReservationStatus.ACTIVE

    def _release(self) -> None:
        if self._status is not ReservationStatus.ACTIVE:
            raise ReservationStateError("Освободить можно только активный резерв")
        self._status = ReservationStatus.RELEASED

    def _expire_if_due(self, now: datetime) -> bool:
        if self._status is not ReservationStatus.ACTIVE:
            return False
        if not self._deadline.is_reached_at(now):
            return False
        self._status = ReservationStatus.EXPIRED
        return True

    def _summary(self) -> ReservationSummary:
        return ReservationSummary(
            reservation_id=self._id,
            order_id=self._order_id,
            quantity=self._quantity,
            deadline=self._deadline,
            status=self._status,
        )


class StockItem:
    """Корень агрегата складской позиции."""

    def __init__(
        self,
        stock_item_id: StockItemId,
        warehouse_id: WarehouseId,
        sku: Sku,
        physical_balance: StockBalance,
    ) -> None:
        if not isinstance(stock_item_id, StockItemId):
            raise ReservationStateError("StockItem требует StockItemId")
        if not isinstance(warehouse_id, WarehouseId):
            raise ReservationStateError("StockItem требует WarehouseId")
        if not isinstance(sku, Sku):
            raise ReservationStateError("StockItem требует Sku")
        if not isinstance(physical_balance, StockBalance):
            raise ReservationStateError("StockItem требует StockBalance")
        self._id = stock_item_id
        self._warehouse_id = warehouse_id
        self._sku = sku
        self._physical_balance = physical_balance
        self._reservations: list[StockReservation] = []

    # --- запросы -----------------------------------------------------------

    def id(self) -> StockItemId:
        return self._id

    def warehouse_id(self) -> WarehouseId:
        return self._warehouse_id

    def sku(self) -> Sku:
        return self._sku

    def physical_balance(self) -> StockBalance:
        return StockBalance(self._physical_balance.amount())

    def reservations(self) -> tuple[ReservationSummary, ...]:
        return tuple(r._summary() for r in self._reservations)

    def active_reserved_quantity(self) -> int:
        return sum(
            r.quantity().value() for r in self._reservations if r.is_active()
        )

    def available_quantity(self) -> int:
        return self._physical_balance.amount() - self.active_reserved_quantity()

    def reservation_status(self, reservation_id: ReservationId) -> ReservationStatus:
        return self._find_reservation(reservation_id).status()

    # --- команды -----------------------------------------------------------

    def receive(self, quantity: Quantity) -> None:
        self._physical_balance = self._physical_balance.increase(quantity)

    def write_off(self, quantity: Quantity) -> None:
        next_balance = self._physical_balance.decrease(quantity)
        if next_balance.amount() < self.active_reserved_quantity():
            raise InsufficientAvailableStockError(
                "Физический остаток не может стать меньше активных резервов"
            )
        self._physical_balance = next_balance

    def reserve(
        self,
        reservation_id: ReservationId,
        order_id: OrderId,
        quantity: Quantity,
        deadline: ReservationDeadline,
    ) -> None:
        if any(r.id() == reservation_id for r in self._reservations):
            raise DuplicateReservationError(
                f"ReservationId {reservation_id.value()!r} уже существует"
            )
        if quantity.value() > self.available_quantity():
            raise InsufficientAvailableStockError(
                "Недостаточно доступного остатка для резерва"
            )
        self._reservations.append(
            StockReservation(reservation_id, order_id, quantity, deadline)
        )

    def release_reservation(self, reservation_id: ReservationId) -> None:
        self._find_reservation(reservation_id)._release()

    def expire_reservations(self, now: datetime) -> int:
        expired = 0
        for reservation in self._reservations:
            if reservation._expire_if_due(now):
                expired += 1
        return expired

    # --- внутренние помощники ---------------------------------------------

    def _find_reservation(self, reservation_id: ReservationId) -> StockReservation:
        for reservation in self._reservations:
            if reservation.id() == reservation_id:
                return reservation
        raise ReservationNotFoundError(
            f"Резерв {reservation_id.value()!r} не принадлежит этой позиции"
        )