from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class CatalogItem:
    sku: str
    price: Decimal
    currency: str