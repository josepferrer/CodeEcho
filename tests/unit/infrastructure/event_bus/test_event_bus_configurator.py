import pytest
from src.infrastructure.event_bus.event_bus_configurator import EventBusConfigurator
from src.domain.events.pull_request_synced import PullRequestSynced


class TestEventBusConfigurator:
    """Test cases for EventBusConfigurator"""

    def test_event_mappings_are_complete(self):
        """Should have all expected event mappings"""
        mappings = EventBusConfigurator.get_event_mappings()

        # Verify all expected events are mapped
        assert PullRequestSynced in mappings
        # Add assertions for other expected events

    @pytest.mark.asyncio
    async def test_configure_subscribes_all_handlers(self, clean_event_bus):
        """Should subscribe all handlers correctly"""
        # Configure event bus
        EventBusConfigurator.configure(clean_event_bus)

        # Create test event
        event = PullRequestSynced(repository="test/repo", pr_number=1)

        # Publish event
        await clean_event_bus.publish(event)

        # Verify handlers were called (you might need to modify handlers to track calls)