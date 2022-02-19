"""Tests for development."""
from datetime import date
from typing import Tuple

from domain.model import Batch, OrderLine


def create_batch_and_line(
    sku: str, batch_qty: int, line_qty: int
) -> Tuple[Batch, OrderLine]:
    return (
        Batch(ref="batch-001", sku=sku, qty=batch_qty, eta=date.today()),
        OrderLine(order_id="order-123", sku=sku, qty=line_qty),
    )


def test_allocation_reduces_batch_available_quantity() -> None:
    test_batch, test_order_line = create_batch_and_line(
        sku="SMALL-TABLE", batch_qty=20, line_qty=2
    )

    test_batch.allocate(test_order_line)

    assert test_batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required() -> None:
    large_batch, small_line = create_batch_and_line("ELEGANT-LAMP", 20, 2)
    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_smaller_than_required() -> None:
    small_batch, large_line = create_batch_and_line("ELEGANT-LAMP", 2, 20)
    assert small_batch.can_allocate(large_line) is False


def test_can_allocate_if_available_equal_to_required() -> None:
    test_batch, test_line = create_batch_and_line("ELEGANT-LAMP", 2, 2)
    assert test_batch.can_allocate(test_line)


def test_cannot_allocate_if_skus_do_not_match() -> None:
    batch = Batch("batch-001", "UNCOMFORTABLE-CHAIR", 100, eta=None)
    different_sku_line = OrderLine("order-123", "EXPENSIVE-TOASTER", 10)
    assert batch.can_allocate(different_sku_line) is False


def test_idempotent_allocation_to_batch() -> None:

    test_batch, test_order_line = create_batch_and_line(
        sku="SMALL-TABLE", batch_qty=20, line_qty=2
    )

    test_batch.allocate(test_order_line)
    test_batch.allocate(test_order_line)

    assert test_batch.available_quantity == 18
