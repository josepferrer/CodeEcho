from typing import Optional
from src.application.events.event_bus import EventBus
from src.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from src.infrastructure.event_bus.event_bus_configurator import EventBusConfigurator


class EventBusProvider:
    """Provider for configured event bus singleton"""

    _instance: Optional[EventBus] = None

    @classmethod
    def get_instance(cls) -> EventBus:
        """Get or create a configured event bus instance"""
        if cls._instance is None:
            event_bus = InMemoryEventBus()
            EventBusConfigurator.configure(event_bus)
            cls._instance = event_bus
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset event bus instance (useful for testing)"""
        cls._instance = None