import pytest
from src.infrastructure.logging.logging_config import setup_logging


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Set up logging for tests."""
    setup_logging()
