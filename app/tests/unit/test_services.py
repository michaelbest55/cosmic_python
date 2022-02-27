"""Functions for testing the service layer."""
from typing import List, Optional

import pytest

import app.domain.model as model
import app.service_layer.services as services
import app.service_layer.unit_of_work as unit_of_work
from app.adapters.repository import AbstractRepository


class FakeRepository(AbstractRepository):
    """Fake for the Repository object."""

    def __init__(self, products: List[model.Product]):
        """Init function.

        Args:
            products: List of Batch entity models.
        """
        self._products = set(products)

    def add(self, product: model.Product) -> None:
        """Add a product to the fake repository.

        Args:
            product: a product aggregate model
        """
        self._products.add(product)

    def get(self, sku: str) -> Optional[model.Product]:
        """Get product from the repository that matches the given sku.

        Args:
            sku: sku that identifies a product.

        Returns:
            The product that matches the sku
        """
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """Fake unit of work for testing."""

    def __init__(self) -> None:
        """Init function."""
        self.products = FakeRepository([])
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


def test_add_batch_for_new_product() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_for_existing_product() -> None:
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    services.add_batch("b2", "CRUNCHY-ARMCHAIR", 99, None, uow)
    product = uow.products.get("CRUNCHY-ARMCHAIR")
    if product:
        assert "b2" in [b.reference for b in product.batches]
    else:
        assert False


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
