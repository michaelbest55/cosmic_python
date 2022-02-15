"""Pytest fixtures for running sqlite."""
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from orm import metadata, start_mappers


@pytest.fixture
def in_memory_db() -> Engine:
    """Create an engine for sqlite in memory db."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db: Engine) -> Generator[sessionmaker, None, None]:
    """Fixture for the tests to create a session in the database.

    Because this gets run in each test function, a clean database is used for the test.
    """
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()
