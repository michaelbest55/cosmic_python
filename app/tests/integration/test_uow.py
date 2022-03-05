"""Tests for the unit of work."""
import threading
import time
import traceback
from typing import Callable, List, Optional, cast

import pytest
from sqlalchemy.orm import Session

from app.domain import model
from app.service_layer import unit_of_work
from app.tests.random_refs import random_batchref, random_orderid, random_sku


def insert_batch(
    session: Session,
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[None],
    product_version: int = 1,
) -> None:
    session.execute(
        "INSERT INTO products (sku, version_number)" " VALUES (:sku, :version_number)",
        dict(sku=sku, version_number=product_version),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(session: Session, orderid: str, sku: str) -> Optional[str]:
    [[orderlineid]] = session.execute(
        "SELECT id FROM order_lines WHERE order_id=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE orderline_id=:orderlineid",
        dict(orderlineid=orderlineid),
    )
    return cast(Optional[str], batchref)


def test_uow_can_retrieve_a_batch_and_allocate_to_it(
    session_factory: Callable[[], Session]
) -> None:
    session = session_factory()
    insert_batch(session, "batch1", "HIPSTER-WORKBENCH", 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku="HIPSTER-WORKBENCH")
        line = model.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        if product:
            product.allocate(line)
            uow.commit()
        else:
            assert False

    batchref = get_allocated_batch_ref(session, "o1", "HIPSTER-WORKBENCH")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(
    session_factory: Callable[[], Session]
) -> None:
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory: Callable[[], Session]) -> None:
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def try_to_allocate_factory(
    orderid: str, sku: str, exceptions: List[Exception]
) -> Callable[[], None]:
    def try_to_allocate() -> None:
        line = model.OrderLine(orderid, sku, 10)
        try:
            with unit_of_work.SqlAlchemyUnitOfWork() as uow:
                product = uow.products.get(sku=sku)
                if product:
                    product.allocate(line)
                    time.sleep(0.2)
                    uow.commit()
                else:
                    raise ValueError(f"No such product with {sku=}")
        except Exception as e:
            print(traceback.format_exc())
            exceptions.append(e)

    return try_to_allocate


@pytest.mark.non_postgres_tests
def test_concurrent_updates_to_version_are_not_allowed(
    postgres_session_factory: Callable[[], Session]
) -> None:
    sku, batch = random_sku(), random_batchref()
    session = postgres_session_factory()
    insert_batch(session, batch, sku, 100, eta=None, product_version=1)
    session.commit()

    order1, order2 = random_orderid("1"), random_orderid("2")
    exceptions: List[Exception] = []
    try_to_allocate_order1 = try_to_allocate_factory(order1, sku, exceptions)
    try_to_allocate_order2 = try_to_allocate_factory(order2, sku, exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        dict(sku=sku),
    )
    assert version == 2
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)

    orders = session.execute(
        "SELECT order_id FROM allocations"
        " JOIN batches ON allocations.batch_id = batches.id"
        " JOIN order_lines ON allocations.orderline_id = order_lines.id"
        " WHERE order_lines.sku=:sku",
        dict(sku=sku),
    )
    assert orders.rowcount == 1
    with unit_of_work.SqlAlchemyUnitOfWork() as uow:
        cast(unit_of_work.SqlAlchemyUnitOfWork, uow).session.execute("select 1")
