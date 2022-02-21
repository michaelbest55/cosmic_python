"""Tests for development."""
from datetime import date, timedelta

import pytest

from domain.model import Batch, OrderLine, OutOfStock, allocate
from service_layer import services
from tests.unit.test_services import FakeRepository, FakeSession


def test_allocation_to_warehouse_stock_prefered_to_shipment_batch() -> None:
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 20)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 20, eta=date.today())
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    services.allocate("oref", "RETRO-CLOCK", 5, repo, session)

    assert in_stock_batch.available_quantity == 15
    assert shipment_batch.available_quantity == 20


def test_prefers_earlier_batches() -> None:
    test_batch_today = Batch("batch-today", "CLOCK", 5, eta=date.today())
    test_batch_yesterday = Batch(
        "batch-yesterday", "CLOCK", 5, eta=date.today() - timedelta(days=1)
    )
    repo = FakeRepository([test_batch_today, test_batch_yesterday])
    session = FakeSession()

    services.allocate("order-123", "CLOCK", 2, repo, session)

    assert test_batch_yesterday.available_quantity == 3
    assert test_batch_today.available_quantity == 5


def test_allocate_returns_allocated_batch_ref() -> None:
    test_batch_today = Batch("batch-today", "CLOCK", 5, eta=date.today())
    test_batch_yesterday = Batch(
        "batch-yesterday", "CLOCK", 5, eta=date.today() - timedelta(days=1)
    )
    repo = FakeRepository([test_batch_today, test_batch_yesterday])
    session = FakeSession()

    batch_ref = services.allocate("order-123", "CLOCK", 2, repo, session)

    assert batch_ref == test_batch_yesterday.reference


def test_raises_out_of_stock_exception() -> None:
    test_batch = Batch("batch-123", "RETRO-CLOCK", 20, eta=date.today())
    repo = FakeRepository([test_batch])
    session = FakeSession()

    services.allocate("order-1", "RETRO-CLOCK", 20, repo, session)
    test_line_2 = OrderLine("order-2", "RETRO-CLOCK", 20)

    with pytest.raises(OutOfStock, match="RETRO-CLOCK"):
        allocate(test_line_2, [test_batch])
