class DomainError(Exception): pass
class InvalidValueError(DomainError): pass
class OrderStateError(DomainError): pass
class CurrencyMismatchError(DomainError): pass
class OrderCannotBePlacedError(DomainError): pass
class PaymentStateError(DomainError): pass