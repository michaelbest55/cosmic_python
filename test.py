
from datetime import date
from typing import Tuple

import pytest

from model import Batch, OrderLine

def create_batch_and_line(sku: str, batch_qty: int, line_qty: int) -> Tuple[Batch, OrderLine]:
    return (Batch(ref="batch-001", sku=sku, batch_qty=batch_qty, eta=date.today()), OrderLine(orderid="order-123", sku=sku, qty=line_qty))

def test_allocation_reduces_batch_available_quantity():
    test_batch, test_order_line = create_batch_and_line(sku="SMALL-TABLE", batch_qty=20, line_qty=2)
    
    test_batch.allocate(test_order_line)

    assert test_batch.available_quantity == 18

def test_cant_allocate_to_batch_if_order_line_too_big():
    test_batch, test_order_line = create_batch_and_line(sku="BLUE-CUSHION", batch_qty=1, line_qty=2)
    test_batch.allocate(test_order_line)

    assert pytest.raises(ValueError)

def test_can_allocate_to_batch_if_order_line_same_size():
    test_batch, test_order_line = create_batch_and_line(sku="SMALL-TABLE", batch_qty=20, line_qty=20)
    
    test_batch.allocate(test_order_line)

    assert test_batch.available_quantity == 0

def test_idempotent_allocation_to_batch():

    test_batch, test_order_line = create_batch_and_line(sku="SMALL-TABLE", batch_qty=20, line_qty=2)
    
    test_batch.allocate(test_order_line)
    test_batch.allocate(test_order_line)

    assert test_batch.available_quantity == 18

def test_allocation_to_warehouse_stock_prefered_to_shipment_batch():
    test_batch, test_order_line = create_batch_and_line(sku="SMALL-TABLE", batch_qty=20, line_qty=2)    
    pytest.fail("todo") 
