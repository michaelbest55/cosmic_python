"""How to store and process events."""
import logging
from typing import Callable, Dict, List, Optional, Type, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential

from app.domain import commands, events
from app.service_layer import handlers, unit_of_work

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


def handle(
    message: Message, uow: unit_of_work.AbstractUnitOfWork
) -> List[Optional[str]]:
    """Handle any message, be it a command or an event.

    Args:
        message: message to process
        uow: class that abstracts atomic operations related to i/o of data

    Returns:
        List of results returns by the command handlers.

    """
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} was not an Event or Command")
    return results


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
) -> Optional[str]:
    """Handler for commands. Different than the event handler as this raises errors.

    Args:
        command: command to be executed
        queue: List of messages that still need to be processed
        uow: class that abstracts atomic operations related to i/o of data

    Returns:
        List of results returned from the handlers
    """
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Handler for events.

    Args:
        event: event to be processed
        queue: List of messages that still need to be processed
        uow: class that abstracts atomic operations related to i/o of data
    """
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3), wait=wait_exponential()
            ):
                with attempt:
                    logger.debug("handling event %s with handler %s", event, handler)
                    handler(event, uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logger.error(
                "Failed to handle event %s times, giving up!",
                retry_failure.last_attempt.attempt_number,
            )
            continue


EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}

COMMAND_HANDLERS: Dict[Type[commands.Command], Callable[..., Optional[str]]] = {
    commands.CreateBatch: handlers.add_batch,
    commands.Allocate: handlers.allocate,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}
