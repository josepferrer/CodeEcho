from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest
import logging

from src.application.services.sync_pull_requests_service import SyncPullRequestsService
from src.domain.entities.pull_request import PullRequest
from src.domain.entities.sync_state import SyncState
from src.domain.exceptions.github_exceptions import GitHubNotFoundException, GitHubRateLimitException
from src.domain.value_objects.sync_state import RepositoryId, ProviderType
from src.infrastructure.event_bus.event_bus_provider import EventBusProvider

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_sync_state_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_github_client():
    client = AsyncMock()
    return client


@pytest.fixture
def mock_pr_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def sample_sync_state():
    return SyncState(
        repository_id=RepositoryId(
            owner="test",
            name="repo",
            provider=ProviderType("github")
        ),
        last_synced_pr=100,
        rate_limit=None,
        synchronized=True,
        last_sync_time=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_pull_requests():
    return [
        PullRequest(
            id="1",
            number=101,
            status="open",
            repository="test/repo",
            raw_data={"title": "Test PR 1"}
        ),
        PullRequest(
            id="2",
            number=102,
            status="closed",
            repository="test/repo",
            raw_data={"title": "Test PR 2"}
        )
    ]

@pytest.fixture
def sample_pull_request():
    return PullRequest(
        id="1",
        number=101,
        status="open",
        repository="test/repo",
        raw_data={"title": "Test PR 1"}
    )

@pytest.fixture
def sample_pull_request2():
    return PullRequest(
        id="2",
        number=102,
        status="closed",
        repository="test/repo",
        raw_data={"title": "Test PR 2"}
    )


@pytest.fixture
def event_bus(mock_sync_state_repo, mock_github_client, mock_pr_repo):
    return EventBusProvider.get_instance()

@pytest.fixture
def service(mock_sync_state_repo, mock_github_client, mock_pr_repo, event_bus):
    return SyncPullRequestsService(
        mock_sync_state_repo,
        mock_github_client,
        mock_pr_repo,
        event_bus
    )


@pytest.mark.asyncio
async def test_sync_one_pr(
        service,
        mock_sync_state_repo,
        mock_github_client,
        mock_pr_repo,
        sample_sync_state,
        sample_pull_request
):
    # Setup
    not_found_exception = GitHubNotFoundException("GitHub API rate limit exceeded")
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.return_value = [sample_sync_state]
    mock_github_client.get_pull_request.side_effect = [
        sample_pull_request,
        not_found_exception,
    ]

    # Execute
    await service.sync_repositories()

    # Verify
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.assert_called_once()
    assert mock_github_client.get_pull_request.call_count == 2
    assert sample_sync_state.last_synced_pr == 101

@pytest.mark.asyncio
async def test_sync_two_pr_and_reach_rate_limit(
        service,
        mock_sync_state_repo,
        mock_github_client,
        mock_pr_repo,
        sample_sync_state,
        sample_pull_request,
        sample_pull_request2
):
    # Setup
    now = datetime.now(timezone.utc)
    one_our_later = now + timedelta(hours=1)
    rate_limit_exception = GitHubRateLimitException(int(one_our_later.timestamp()))
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.return_value = [sample_sync_state]
    mock_github_client.get_pull_request.side_effect = [
        sample_pull_request,
        sample_pull_request2,
        rate_limit_exception,
    ]

    # Execute
    await service.sync_repositories()

    # Verify
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.assert_called_once()
    assert mock_github_client.get_pull_request.call_count == 3
    assert sample_sync_state.last_synced_pr == 102
    assert sample_sync_state.rate_limit.is_exceeded(now)
    assert sample_sync_state.rate_limit.reset_time.replace(microsecond=0) == one_our_later.replace(microsecond=0)

@pytest.mark.asyncio
async def test_sync_repositories_with_error(
        service,
        mock_sync_state_repo,
        mock_github_client,
        sample_sync_state
):
    # Setup
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.return_value = [
        sample_sync_state
    ]
    mock_github_client.get_pull_request.side_effect = [Exception("API Error")]

    # Execute
    await service.sync_repositories()

    # Verify service continues despite error
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.assert_called_once()
    mock_github_client.get_pull_request.assert_called_once()
    assert sample_sync_state.last_synced_pr == 100
