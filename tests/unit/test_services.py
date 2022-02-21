"""Functions for testing the service layer."""
from typing import List

import pytest

import domain.model as model
import service_layer.services as services
from adapters.repository import AbstractRepository


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


class FakeSession:
    """Fake class that models a database session."""

    committed = False

    def commit(self) -> None:
        """Function that fakes the commit of a session."""
        self.committed = True


def test_commits() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "OMINOUS-MIRROR", 100, None, repo, session)

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)
    assert session.committed is True


def test_returns_allocations() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)

    result = services.allocate(
        "o1", "COMPLICATED-LAMP", 10, repo, session=FakeSession()
    )
    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, session=FakeSession())


def test_add_batch() -> None:
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed
