"""Module to define all the commands of the app."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


class Command:
    """Generic Command."""

    pass


@dataclass
class Allocate(Command):
    """Command for allocating a line order to a batch."""

    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    """Command for creating a batch."""

    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass
class ChangeBatchQuantity(Command):
    """Command for changing the quantity of a batch."""

    ref: str
    qty: int
