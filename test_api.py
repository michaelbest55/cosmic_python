"""Tests for the flask api endpoints."""
import uuid
from typing import Callable, List, Optional, Tuple

import pytest
import requests

import config


def random_suffix() -> str:
    """Function to get the first six characters of a uuid.

    Returns: generated string
    """
    return uuid.uuid4().hex[:6]


def random_sku(name: str = "") -> str:
    """Sku that is randomly generated.

    Args:
        name: optional string to insert into generated sku

    Returns: generated string
    """
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name: str = "") -> str:
    """Reference to a fake batch that is randomly generated.

    Args:
        name: optional string to insert into generated batch

    Returns: generated string
    """
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name: str = "") -> str:
    """Orderid that is randomly generated.

    Args:
        name: optional string to insert into generated orderid

    Returns: generated string
    """
    return f"order-{name}-{random_suffix}"


@pytest.mark.usefixtures("restart_api")
def test_api_returns_allocation_and_201(
    add_stock: Callable[[List[Tuple[str, str, int, Optional[str]]]], None]
) -> None:
    sku, other_sku = random_sku(), random_sku("other")
    early_batch = random_batchref("1")
    later_batch = random_batchref("2")
    other_batch = random_batchref("3")
    add_stock(
        [
            (later_batch, sku, 100, "2011-01-02"),
            (early_batch, sku, 100, "2011-01-01"),
            (other_batch, other_sku, 100, None),
        ]
    )
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 201
    assert r.json()["batchref"] == early_batch


@pytest.mark.usefixtures("restart_api")
def test_bad_call_returns_400_and_error_message() -> None:
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"
