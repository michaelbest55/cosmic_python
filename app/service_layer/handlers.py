"""Definition of service layer functions."""
from typing import Optional, Protocol

import app.domain.model as model
from app.domain import commands, events
from app.service_layer import unit_of_work


class InvalidSku(Exception):
    """Exception to be raised.

    Exception when trying to allocate a line batch to batches
    that don't have the corresponding sku.
    """

    pass


class InvalidBatchRef(Exception):
    """Exception to be raised.

    Exception when trying to get a product by batchref that does not exist.
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
    command: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service layer function to add a batch given the input necessary.

    This decouples the service-layer functions from the domain.

    Args:
        command: create batch command
        ouw: class that abstracts atomic operations related to i/o of data

    Returns:
        None
    """
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            model.Batch(command.ref, command.sku, command.qty, command.eta)
        )
        uow.commit()


def allocate(
    command: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> Optional[str]:
    """Allocate an orderline to an appropriate batch.

    Args:
        command: allocate command
        ouw: class that abstracts atomic operations related to i/o of data

    Returns:
        batchref: batchref of the batch to which the line was allocated

    Raises:
        InvalidSku: in the case that the sku of line is not found in any of the
        batches of the repo
    """
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def change_batch_quantity(
    command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork
) -> None:
    """Change the initial amount of a batch.

    Args:
        command: command with the batchref and amount to change to
        uow: class that abstracts atomic operations related to i/o of data

    Raises:
        InvalidBatchRef: in the case where the batchref does not match a batch in
        the system
    """
    with uow:
        product = uow.products.get_by_batchref(batchref=command.ref)
        if product is None:
            raise InvalidBatchRef(f"Invalid batchref {command.ref}")
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


def send_out_of_stock_notification(
    event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork
) -> None:
    """Notify users that an out of stock event was raised."""
    pass
