import pytest
from src.infrastructure.logging.logging_config import setup_logging
from tests.helpers.event_bus_test_helper import EventBusTestHelper


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Set up logging for tests."""
    setup_logging()

@pytest.fixture
def clean_event_bus():
    """Provide a clean event bus instance"""
    return EventBusTestHelper.get_clean_event_bus()


@pytest.fixture
def configured_event_bus():
    """Provide a configured event bus instance"""
    return EventBusTestHelper.get_configured_event_bus()