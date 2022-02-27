"""Definition of service layer functions."""
from datetime import date
from typing import Optional, Protocol

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
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(ref, sku, qty, eta))
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
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref
