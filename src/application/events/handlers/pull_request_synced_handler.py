import logging
from src.application.events.event_bus import EventBus
from src.domain.events.pull_request_synced import PullRequestSynced

logger = logging.getLogger(__name__)


class PullRequestSyncedHandler:
    """Handler for PullRequestSynced event."""

    async def handle(event: PullRequestSynced):
        logger.debug(f"Processing PR sync event: {event.repository} PR#{event.number} raw data: {event.raw_data} ")
        # Aquí podrías guardar datos en una base de datos o realizar otra acción.
