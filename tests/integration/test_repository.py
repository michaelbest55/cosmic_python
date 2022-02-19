"""Unit tests for the SqlAlchemyRepository."""
from sqlalchemy.orm.session import Session

import domain.model as model
from adapters.repository import SqlAlchemyRepository


def test_repository_can_save_a_batch(session: Session) -> None:
    batch = model.Batch(ref="batch1", sku="NIFTY-COUCH", qty=10)

    repo = SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        "SELECT reference, sku, _purchased_quantity, eta FROM batches"
    )
    assert list(rows) == [("batch1", "NIFTY-COUCH", 10, None)]
