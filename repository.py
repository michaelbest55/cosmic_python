"""Implementations of the repositories for the domain."""
import abc

from sqlalchemy.orm.session import Session

import model


class AbstractRepository(abc.ABC):
    """Interface for a Repository."""

    @abc.abstractmethod
    def add(self, batch: model.Batch) -> None:
        """Add a batch to the repository.

        Args:
            batch: batch model to add to the repository.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str) -> model.Batch:
        """Get a batch from a repository.

        Args:
            reference: reference of the batch to retrieve
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

    def add(self, batch: model.Batch) -> None:
        """Add a batch to the repository.

        Args:
            batch: model to add
        """
        self.session.add(batch)

    def get(self, reference: str) -> model.Batch:
        """Get a batch from the repository.

        Args:
            reference: str with the reference of the batch
        """
        return self.session.query(model.Batch).filter_by(reference=reference).one()
