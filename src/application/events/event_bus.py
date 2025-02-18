from abc import ABC, abstractmethod
from typing import Type, Callable

from src.application.events.event import Event


class EventBus(ABC):
    """Interfaz para un Bus de Eventos."""

    @abstractmethod
    def subscribe(self, event_type: Type[Event], handler: Callable):
        """Suscribe un handler a un tipo de evento."""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: Type[Event], handler: Callable) -> None:
        """Unsubscribe a handler from an event type"""
        pass

    @abstractmethod
    async def publish(self, event: Event):
        """Publica un evento en el bus."""
        pass