"""Definition of service layer functions."""
from datetime import date
from typing import List, Optional, Protocol

import app.domain.model as model
from app.service_layer import unit_of_work


class InvalidSku(Exception):
    """Exception to be raised.

    Exception when trying to allocate a line batch to batches
    that don't have the corresponding sku.
    """

    pass


class SessionProtocol(Protocol):
    """Ensure that a session has a commit method.

    This is required as we might want to fake a sql alchemy session.
    """

    def commit(self) -> None:
        """A session must have a commit method."""
        raise NotImplementedError


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    """Check if sku belongs to any of the given batches.

    Args:
        sku: value to check
        batches: list of batches to check

    Returns:
        true if sku is in any of the batches
    """
    return sku in {b.sku for b in batches}


def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service layer function to add a batch given the input necessary.

    This decouples the service-layer functions from the domain.

    Args:
        ref: string with the batch reference
        sku: str with the stock keeping unit
        qty: amount of units for the batch
        eta: date of arrival at warehouse
        ouw: class that abstracts atomic operations related to i/o of data

    Returns:
        None
    """
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    """Allocate an orderline to an appropriate batch.

    Args:
        ref: string with the batch reference
        sku: str with the stock keeping unit
        qty: amount of units for the batch
        eta: date of arrival at warehouse
        ouw: class that abstracts atomic operations related to i/o of data

    Returns:
        batchref: batchref of the batch to which the line was allocated

    Raises:
        InvalidSku: in the case that the sku of line is not found in any of the
        batches of the repo
    """
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref
