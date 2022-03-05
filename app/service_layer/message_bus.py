"""How to store and process events."""
from typing import Callable, Dict, List

from app.domain import events


def handle(event: events.Event) -> None:
    """For each type of event handler, pass all of the events it needs to process."""
    for handler in HANDLERS[event]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock) -> None:
    """Notify users that an out of stock event was raised."""
    pass


HANDLERS: Dict[events.Event, List[Callable[[events.Event], None]]] = {
    events.OutOfStock: [send_out_of_stock_notification],  # type: ignore
}
