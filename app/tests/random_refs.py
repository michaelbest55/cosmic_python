"""Helper functions that I don't want to use as fixtures."""
import uuid


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
    return f"order-{name}-{random_suffix()}"
