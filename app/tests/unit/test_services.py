"""Functions for testing the service layer."""
from typing import List

import pytest

import app.domain.model as model
import app.service_layer.services as services
import app.service_layer.unit_of_work as unit_of_work
from app.adapters.repository import AbstractRepository


class FakeRepository(AbstractRepository):
    """Fake for the Repository object."""

    def __init__(self, batches: List[model.Batch]):
        """Init function.

        Args:
            batches: List of Batch entity models.
        """
        self._batches = set(batches)

    def add(self, batch: model.Batch) -> None:
        """Add a batch to the fake repository.

        Args:
            batch: a Batch entity model
        """
        self._batches.add(batch)

    def get(self, reference: str) -> model.Batch:
        """Get batches from the repository that match the given reference.

        Args:
            reference: str that identifies a batch.

        Returns:
            A generator with all the batches that match the reference
        """
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> List[model.Batch]:
        """Returns a list of batches from the repository.

        Returns:
            List of batches in the repository
        """
        return list(self._batches)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """Fake unit of work for testing."""

    def __init__(self) -> None:
        """Init function."""
        self.batches = FakeRepository([])
        self.committed = False

    def commit(self) -> None:
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


def test_add_batch() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_allocate_commits() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
    services.allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert uow.committed
