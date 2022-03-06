"""Functions for testing the service layer."""
from datetime import date
from typing import List, Optional, Set

import pytest

import app.domain.model as model
import app.service_layer.handlers as handlers
import app.service_layer.unit_of_work as unit_of_work
from app.adapters.repository import AbstractRepository
from app.domain import commands
from app.service_layer import message_bus


class FakeRepository(AbstractRepository):
    """Fake for the Repository object."""

    def __init__(self, products: List[model.Product]):
        """Init function.

        Args:
            products: List of Batch entity models.
        """
        super().__init__()
        self._products = set(products)

    def _add(self, product: model.Product) -> None:
        """Add a product to the fake repository.

        Args:
            product: a product aggregate model
        """
        self._products.add(product)

    def _get(self, sku: str) -> Optional[model.Product]:
        """Get product from the repository that matches the given sku.

        Args:
            sku: sku that identifies a product.

        Returns:
            The product that matches the sku
        """
        return next((p for p in self._products if p.sku == sku), None)

    def list(self) -> Set[model.Product]:
        """Get the set of products associated to a repo.

        Returns:
            The set of products.
        """
        return self._products

    def _get_by_batchref(self, batchref: str) -> Optional[model.Product]:
        """Get a product by batchref.

        Args:
            batchref: a batchref string

        Returns:
            product
        """
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """Fake unit of work for testing."""

    def __init__(self) -> None:
        """Init function."""
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self) -> None:
        """How to commit."""
        self.committed = True

    def rollback(self) -> None:
        """How to rollback."""
        pass


class FakeSession:
    """Fake class that models a database session."""

    committed = False

    def commit(self) -> None:
        """Function that fakes the commit of a session."""
        self.committed = True


class TestBatch:
    """Group of tests related to handling batches."""

    def test_add_batch_for_new_product(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(
            commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None), uow
        )
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_add_batch_for_existing_product(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(
            commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None), uow
        )
        message_bus.handle(
            commands.CreateBatch("b2", "CRUNCHY-ARMCHAIR", 99, None), uow
        )
        product = uow.products.get("CRUNCHY-ARMCHAIR")
        if product:
            assert "b2" in [b.reference for b in product.batches]
        else:
            assert False


class TestAllocate:
    """Tests related to handling allocations."""

    def test_allocate_returns_allocation(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(
            commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None), uow
        )
        result = message_bus.handle(
            commands.Allocate("o1", "COMPLICATED-LAMP", 10), uow
        )
        assert result.pop(0) == "batch1"

    def test_allocate_errors_for_invalid_sku(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            message_bus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10), uow)

    def test_allocate_commits(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None), uow)
        message_bus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed


class TestChangeBatchQuantity:
    """Tests related to handling change batch quantity commands."""

    def test_changes_available_quantity(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        assert (test_product := uow.products.get(sku="ADORABLE-SETTEE")) is not None
        [batch] = test_product.batches
        assert batch.available_quantity == 100

        message_bus.handle(commands.ChangeBatchQuantity("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_raises_invalid_batchref(self) -> None:
        uow = FakeUnitOfWork()
        message_bus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        with pytest.raises(handlers.InvalidBatchRef, match="Invalid batchref batch2"):
            message_bus.handle(commands.ChangeBatchQuantity("batch2", 10), uow)

    def test_reallocates_if_necessary(self) -> None:
        uow = FakeUnitOfWork()
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            message_bus.handle(e, uow)
        assert (test_product := uow.products.get(sku="INDIFFERENT-TABLE")) is not None
        [batch1, batch2] = test_product.batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        message_bus.handle(commands.ChangeBatchQuantity("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
