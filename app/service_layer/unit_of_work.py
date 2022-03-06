"""Module for the unit of work, this abstracts the idea of atomic operations.

This module is coupled to the repository.
"""
from __future__ import annotations

import abc
from typing import Any, Callable, Generator, Union

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.config as config
from app.adapters import repository
from app.domain import commands, events

DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
        isolation_level="REPEATABLE READ",
    ),
)

Message = Union[commands.Command, events.Event]


class AbstractUnitOfWork(abc.ABC):
    """Abstract class defintion, children must have commit and rollback methods."""

    products: repository.AbstractRepository

    def __enter__(self, *args: Any) -> AbstractUnitOfWork:
        """How to use the class in a context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """What to do when exiting a context."""
        self.rollback()

    def commit(self) -> None:
        """How to commit work and publish events."""
        self._commit()

    @abc.abstractmethod
    def _commit(self) -> None:
        """How to commit work to the persistent storage."""
        raise NotImplementedError

    def collect_new_events(self) -> Generator[Message, None, None]:
        """Event handler."""
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    @abc.abstractmethod
    def rollback(self) -> None:
        """How to roll work back from the persistent storage."""
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unit of work for a sqlalchemy engine."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = DEFAULT_SESSION_FACTORY,
    ):
        """Init method.

        Args:
            session_factory: Callable that returns a sqlalchemy session
        """
        self.session_factory = session_factory

    def __enter__(self, *args: Any) -> AbstractUnitOfWork:
        """Return a unit of work subclass when entering a context manager."""
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args: Any) -> None:
        """Close the session after rolling back."""
        super().__exit__(*args)
        self.session.close()

    def _commit(self) -> None:
        """Commit the work to the sqlalchemy session."""
        self.session.commit()

    def rollback(self) -> None:
        """How to perform a rollback."""
        self.session.rollback()
