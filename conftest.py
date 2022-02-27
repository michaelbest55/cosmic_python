"""Extra conftest sp custom cli option can be interpreted by pytest correctly."""
from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--non_postgres_tests",
        action="store_true",
        default=False,
        help="run tests that don't use postgres",
    )


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "non_postgres_tests: mark test as not needed for pre-commit",
    )


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    if not config.getoption("--non_postgres_tests"):
        # --non_postgres_tests given in cli: skip non_postgres_tests tests
        return
    skip_non_postgres_tests = pytest.mark.skip(reason="--non_postgres_tests given")
    for item in items:
        if "non_postgres_tests" in item.keywords:
            item.add_marker(skip_non_postgres_tests)
