from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import uuid4

@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: str

@dataclass
class Batch:
    ref: str
    sku: str
    eta: Optional[date]
    available_quantity: int

    def allocate(self, line: OrderLine) -> None:
        self.available_quantity -= line.qty
