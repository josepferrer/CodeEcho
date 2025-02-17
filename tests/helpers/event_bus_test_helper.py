from typing import Type, List
from src.application.events.event import Event
from src.application.events.event_bus import EventBus
from src.infrastructure.event_bus.event_bus_provider import EventBusProvider


class EventBusTestHelper:
    """Helper for testing event bus related functionality"""

    @staticmethod
    def get_clean_event_bus() -> EventBus:
        """Get a clean event bus instance without default subscriptions"""
        EventBusProvider.reset()
        return EventBusProvider.get_instance()

    @staticmethod
    def get_configured_event_bus() -> EventBus:
        """Get an event bus instance with all default subscriptions"""
        return EventBusProvider.get_instance()