"""Pytest fixtures for running sqlite."""
import time
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple, cast

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

import app.config as config
from app.adapters.orm import metadata, start_mappers


@pytest.fixture
def in_memory_db() -> Engine:
    """Create an engine for sqlite in memory db."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(in_memory_db: Engine) -> Generator[sessionmaker, None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture
def session(session_factory: sessionmaker) -> Session:
    return cast(Session, session_factory())


def wait_for_postgres_to_come_up(engine: Engine) -> Connection:
    """Wait for connection to postgres.

    Args:
        engine: sqlalchemy engine
    """
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


def wait_for_webapp_to_come_up() -> requests.Response:
    """Wait until flask app is running."""
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")


@pytest.fixture(scope="session")
def postgres_db() -> Engine:
    """Fixture function for creating a postgres engine.

    Returns:
        The engine
    """
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(
    postgres_db: Engine,
) -> Generator[Callable[[], Session], None, None]:
    start_mappers()
    yield sessionmaker(bind=postgres_db)
    clear_mappers()


@pytest.fixture
def postgres_session(postgres_session_factory: Callable[[], Session]) -> Session:
    return postgres_session_factory()


@pytest.fixture
def add_stock(
    postgres_session: Session,
) -> Generator[Callable[[List[Tuple[str, str, int, Optional[str]]]], None], None, None]:
    """Fixture that returns a callable for adding stock into a repository.

    Once the function calling the fixture is done, the inserted data is deleted.

    Args:
        postgres_session: Session to run queries on

    Returns:
        _add_stock callable
    """
    batches_added = set()
    skus_added = set()

    def _add_stock(lines: List[Tuple[str, str, int, Optional[str]]]) -> None:
        for ref, sku, qty, eta in lines:
            postgres_session.execute(
                "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                " VALUES (:ref, :sku, :qty, :eta)",
                dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = postgres_session.execute(
                "SELECT id FROM batches WHERE reference=:ref AND sku=:sku",
                dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        postgres_session.execute(
            "DELETE FROM allocations WHERE batch_id=:batch_id",
            dict(batch_id=batch_id),
        )
        postgres_session.execute(
            "DELETE FROM batches WHERE id=:batch_id",
            dict(batch_id=batch_id),
        )
    for sku in skus_added:
        postgres_session.execute(
            "DELETE FROM order_lines WHERE sku=:sku",
            dict(sku=sku),
        )
        postgres_session.commit()


@pytest.fixture
def restart_api() -> None:
    """Util to restart the flask app by updating the access time."""
    (Path(__file__).parent / "flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()
