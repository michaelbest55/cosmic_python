"""Definition of service layer functions."""
from datetime import date
from typing import List, Optional, Protocol

import domain.model as model
from adapters.repository import AbstractRepository


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
    repo: AbstractRepository,
    session: SessionProtocol,
) -> None:
    """Service layer function to add a batch given the input necessary.

    This decouples the service-layer functions from the domain.

    Args:
        ref: string with the batch reference
        sku: str with the stock keeping unit
        qty: amount of units for the batch
        eta: date of arrival at warehouse
        repo: repository abstraction for saving the data
        session: How to commit transactions in the repo to the data layer

    """
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()


def allocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session: SessionProtocol
) -> str:
    """Allocate an orderline to an appropriate batch.

    Args:
        line: A orderline model
        repo: a repository from which to get batches
        session: a database session

    Returns:
        batchref: batchref of the batch to which the line was allocated

    Raises:
        InvalidSku: in the case that the sku of line is not found in any of the
        batches of the repo
    """
    batches = repo.list()
    line = model.OrderLine(orderid, sku, qty)
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref
