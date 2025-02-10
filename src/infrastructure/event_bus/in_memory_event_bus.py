from typing import Dict, List, Type, Callable
from src.application.events.event_bus import EventBus
from src.application.events.event import Event


class InMemoryEventBus(EventBus):
    """Bus de eventos en memoria."""

    def __init__(self):
        self._subscribers: Dict[Type[Event], List[Callable]] = {}

    def subscribe(self, event_type: Type[Event], handler: Callable):
        """Registra un handler para un tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event):
        """Publica un evento y notifica a los handlers suscritos."""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)