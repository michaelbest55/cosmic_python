"""Implementations of the repositories for the domain."""
import abc
from typing import Optional, Set, cast

from sqlalchemy.orm.session import Session

import app.domain.model as model
from app.adapters import orm


class AbstractRepository(abc.ABC):
    """Interface for a Repository."""

    def __init__(self) -> None:
        """Init function. Adds a set of seen products."""
        self.seen: Set[model.Product] = set()

    def add(self, product: model.Product) -> None:
        """Add a product to the repository.

        Args:
            product: product model to add to the repository.
        """
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> Optional[model.Product]:
        """Get a product from a repository.

        Args:
            sku: sku of the product to retrieve
        """
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref: str) -> Optional[model.Product]:
        """Get a product based on the given batchref.

        Args:
            batchref: str with the ref of the batch of a product

        Returns:
            Product if it exists
        """
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: model.Product) -> None:
        """Add a product to the repository.

        Args:
            product: product model to add to the repository.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku: str) -> Optional[model.Product]:
        """Get a product from a repository.

        Args:
            sku: sku of the product to retrieve
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_batchref(self, batchref: str) -> Optional[model.Product]:
        """Get a product from a repository by using a batch reference.

        Args:
            batchref: how to identify the batch

        Returns:
            product associated to a batch
        """
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """Instance of the Repository interface for SqlAlchemy."""

    def __init__(self, session: Session) -> None:
        """Initialize a sqlalchemy repository object.

        Args:
            session: SqlAlchemy session to attach the repository to.
        """
        super().__init__()
        self.session = session

    def _add(self, product: model.Product) -> None:
        """Add a product to the repository.

        Args:
            product: model to add
        """
        self.session.add(product)

    def _get(self, sku: str) -> Optional[model.Product]:
        """Get a product from the repository.

        Args:
            sku: str with the sku of the product

        Returns:
            Product that is chosen
        """
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batchref(self, batchref: str) -> Optional[model.Product]:
        """Get a product from a repository by using a batch reference.

        Args:
            batchref: how to identify the batch

        Returns:
            product associated to a batch
        """
        return cast(
            Optional[model.Product],
            self.session.query(model.Product)
            .join(model.Batch)
            .filter(orm.batches.c.reference == batchref)
            .first(),
        )
