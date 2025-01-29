import pytest
import os
from dotenv import load_dotenv


def pytest_configure(config):
    """Load environment variables at the start of tests"""
    load_dotenv()
    print("pytest_configure")
    print(os.getenv('GITHUB_TOKEN'))
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


@pytest.fixture
def test_repository():
    """Repository to use for testing"""
    return "facebook/react"



