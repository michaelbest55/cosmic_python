"""Tests for the flask api endpoints."""
from typing import Optional

import pytest
import requests

import app.config as config
from app.tests.random_refs import random_batchref, random_orderid, random_sku


@pytest.mark.non_postgres_tests
@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_api_returns_allocation_and_201() -> None:
    sku, other_sku = random_sku(), random_sku("other")
    early_batch = random_batchref("1")
    later_batch = random_batchref("2")
    other_batch = random_batchref("3")
    post_to_add_batch(later_batch, sku, 100, "2011-01-02")
    post_to_add_batch(early_batch, sku, 100, "2011-01-01")
    post_to_add_batch(other_batch, other_sku, 100, None)

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == early_batch


@pytest.mark.non_postgres_tests
@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_bad_call_returns_400_and_error_message() -> None:
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"


def post_to_add_batch(ref: str, sku: str, qty: int, eta: Optional[str]) -> None:
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == 201
