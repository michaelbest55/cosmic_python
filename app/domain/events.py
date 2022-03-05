"""Module to implement all of the expected events for the app."""
from dataclasses import dataclass


class Event:
    """Generic Event class."""

    pass


@dataclass
class OutOfStock(Event):
    """An event that is raised when there is no more stock for a batch."""

    sku: str
