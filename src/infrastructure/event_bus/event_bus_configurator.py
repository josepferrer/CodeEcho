from typing import Dict, Type, Callable
from src.application.events.event import Event
from src.application.events.event_bus import EventBus
from src.application.events.handlers.pull_request_synced_handler import PullRequestSyncedHandler
from src.domain.events.pull_request_synced import PullRequestSynced


class EventBusConfigurator:
    """Configures event subscriptions for the event bus"""

    @classmethod
    def get_event_mappings(cls) -> Dict[Type[Event], list[Callable]]:
        """
        Define all event-handler mappings in one place.
        This makes it easy to see all event subscriptions at a glance.
        """
        return {
            PullRequestSynced: [PullRequestSyncedHandler.handle],
            # Add more event-handler mappings here
        }

    @classmethod
    def configure(cls, event_bus: EventBus) -> None:
        """Configure all event subscriptions"""
        for event_type, handlers in cls.get_event_mappings().items():
            for handler in handlers:
                event_bus.subscribe(event_type, handler)