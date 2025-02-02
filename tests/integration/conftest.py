import os

import pytest
from dotenv import load_dotenv
from src.infrastructure.logging.logging_config import setup_logging


def pytest_configure(config):
    """Load environment variables at the start of tests"""
    load_dotenv()

    # Verify GitHub token exists
    if not os.getenv('GITHUB_TOKEN'):
        raise ValueError(
            "GITHUB_TOKEN environment variable is required for integration tests. "
            "Please set it in your .env file or environment variables."
        )


@pytest.fixture
def github_token():
    """Provide GitHub token from environment variables"""
    return os.getenv('GITHUB_TOKEN')


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Set up logging for tests."""
    setup_logging()
