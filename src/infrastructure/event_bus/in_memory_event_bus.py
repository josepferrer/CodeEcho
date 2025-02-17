# src/infrastructure/event_bus/in_memory_event_bus.py
from typing import Dict, List, Type, Callable, Any
import logging
from src.application.events.event import Event
from src.application.events.event_bus import EventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """In-memory implementation of event bus"""

    def __init__(self):
        self._handlers: Dict[Type[Event], List[Callable]] = {}

    def subscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.
        If a handler raises an exception, it will be logged and other handlers
        will still be executed.
        """
        event_type = type(event)
        if event_type not in self._handlers:
            return

        for handler in self._handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Error handling event {event_type.__name__}: {str(e)}",
                    exc_info=True
                )