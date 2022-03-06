"""Models of the domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, List, Optional, Set, Union

from app.domain import commands, events

Message = Union[commands.Command, events.Event]


class Product:
    """Aggregate model."""

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        """Initialization of a product.

        Args:
            sku: str with the stock keeping unit of the prodcut
            batches: list of batches of an sku
            version_number: integer that helps on deceding which
            transaction should be commited to a database
        """
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events: List[Message] = []

    def allocate(self, line: OrderLine) -> Optional[str]:
        """Allocate an orderline to a product.

        Args:
            line: an order line to allocate to a product

        Returns:
            reference of the batch to which the line was allocated to.
        """
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None

    def change_batch_quantity(self, ref: str, qty: int) -> None:
        """Change the quantity in a batch.

        Args:
            ref: reference of the batch
            qty: new quantity in the batch

        """
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(commands.Allocate(line.order_id, line.sku, line.qty))


@dataclass(unsafe_hash=True)
class OrderLine:
    """Model of an order line, this corresponds to a value object."""

    order_id: str
    sku: str
    qty: int


class Batch:
    """Model of a Batch. Batches are an entity."""

    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date] = None):
        """Initialization of a batch object.

        Args:
            ref: the uid of the object
            sku: stock keeping unit
            qty: initial ammount of purchased qty for a batch
            eta: estimate date of arrival of a batch if it is shipping,
            None if it is in a warehouse

        """
        self.reference = ref
        self.sku = sku
        self._purchased_quantity = qty
        self.eta = eta
        # Note to self, this is a candidate for a command pattern
        self._allocations: Set[OrderLine] = set()

    def __eq__(self, other: Any) -> bool:
        """Check if a Batch object and a different object are equal.

        Args:
            other: another python object

        """
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self) -> int:
        """Hash function based on the reference of an object."""
        return hash(self.reference)

    def __gt__(self, other: Batch) -> bool:
        """Greater than is based on the eta."""
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def can_allocate(self, line: OrderLine) -> bool:
        """Check whether an order line can be allocated to batch.

        Args:
            line: Order line to test.

        Returns:
            True when the line can be allocated
        """
        return self.available_quantity >= line.qty and self.sku == line.sku

    def allocate(self, line: OrderLine) -> None:
        """Allocate an order line to a batch.

        Args:
            line: Order line to allocate to the batch.

        """
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        """Deallocate an order line to a batch.

        Args:
            line: Order line to allocate to the batch.

        """
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> OrderLine:
        """Deallocate the first order line in a batch.

        Returns:
            the deallocated orderline
        """
        return self._allocations.pop()

    @property
    def allocated_quantity(self) -> int:
        """Get the sum of the allocated order lines quantities for a batch.

        Returns:
            result
        """
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        """Property with the available quantity of an sku from a batch.

        Returns: result
        """
        return self._purchased_quantity - self.allocated_quantity
