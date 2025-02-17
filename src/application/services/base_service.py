from src.application.events.event_bus import EventBus


class BaseService:
    """Base class for application services"""

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus