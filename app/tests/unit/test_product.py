"""Tests for development."""
from datetime import date, timedelta

import pytest

from app.domain.model import Batch, OrderLine, OutOfStock, Product


def test_prefers_earlier_batches() -> None:
    test_batch_today = Batch("batch-today", "CLOCK", 5, eta=date.today())
    test_batch_yesterday = Batch(
        "batch-yesterday", "CLOCK", 5, eta=date.today() - timedelta(days=1)
    )
    product = Product("CLOCK", [test_batch_yesterday, test_batch_today])
    test_line = OrderLine("oref", "CLOCK", 2)

    product.allocate(test_line)

    assert test_batch_yesterday.available_quantity == 3
    assert test_batch_today.available_quantity == 5


def test_allocate_returns_allocated_batch_ref() -> None:
    test_batch_today = Batch("batch-today", "CLOCK", 5, eta=date.today())
    test_batch_yesterday = Batch(
        "batch-yesterday", "CLOCK", 5, eta=date.today() - timedelta(days=1)
    )
    product = Product("CLOCK", [test_batch_today, test_batch_yesterday])
    test_line = OrderLine("oref", "CLOCK", 5)
    batch_ref = product.allocate(test_line)

    assert batch_ref == test_batch_yesterday.reference


def test_raises_out_of_stock_exception() -> None:
    test_batch = Batch("batch-123", "RETRO-CLOCK", 20, eta=date.today())
    test_line = OrderLine("oref", "RETRO-CLOCK", 20)
    product = Product("RETRO-CLOCK", [test_batch])
    product.allocate(test_line)
    test_line_2 = OrderLine("order-2", "RETRO-CLOCK", 20)

    with pytest.raises(OutOfStock, match="RETRO-CLOCK"):
        product.allocate(test_line_2)


def test_allocation_to_warehouse_stock_prefered_to_shipment_batch() -> None:
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 20)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 20, eta=date.today())
    product = Product("RETRO-CLOCK", [in_stock_batch, shipment_batch])
    test_line = OrderLine("oref", "RETRO-CLOCK", 5)

    product.allocate(test_line)

    assert in_stock_batch.available_quantity == 15
    assert shipment_batch.available_quantity == 20


def test_increments_version_number() -> None:
    line = OrderLine("oref", "SCANDI-PEN", 10)
    product = Product(
        sku="SCANDI-PEN", batches=[Batch("b1", "SCANDI-PEN", 100, eta=None)]
    )
    product.version_number = 7
    product.allocate(line)
    assert product.version_number == 8
