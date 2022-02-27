"""Implementations of the repositories for the domain."""
import abc
from typing import Optional

from sqlalchemy.orm.session import Session

import app.domain.model as model


class AbstractRepository(abc.ABC):
    """Interface for a Repository."""

    @abc.abstractmethod
    def add(self, product: model.Product) -> None:
        """Add a product to the repository.

        Args:
            product: product model to add to the repository.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku: str) -> Optional[model.Product]:
        """Get a product from a repository.

        Args:
            sku: sku of the product to retrieve
        """
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """Instance of the Repository interface for SqlAlchemy."""

    def __init__(self, session: Session) -> None:
        """Initialize a sqlalchemy repository object.

        Args:
            session: SqlAlchemy session to attach the repository to.
        """
        self.session = session

    def add(self, product: model.Product) -> None:
        """Add a product to the repository.

        Args:
            product: model to add
        """
        self.session.add(product)

    def get(self, sku: str) -> Optional[model.Product]:
        """Get a product from the repository.

        Args:
            sku: str with the sku of the product

        Returns:
            Product that is chosen
        """
        return self.session.query(model.Product).filter_by(sku=sku).first()
