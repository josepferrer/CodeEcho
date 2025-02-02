from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from src.application.services.sync_pull_requests_service import SyncPullRequestsService
from src.domain.entities.pull_request import PullRequest
from src.domain.entities.sync_state import SyncState
from src.domain.value_objects.sync_state import RepositoryId, ProviderType


@pytest.fixture
def mock_sync_state_repo():
    repo = AsyncMock()
    repo.find_outdated_repositories_ready_to_sync = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_github_client():
    client = AsyncMock()
    client.get_pull_requests = AsyncMock()
    return client


@pytest.fixture
def mock_pr_repo():
    repo = AsyncMock()
    repo.save_batch = AsyncMock()
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
        last_sync_time=datetime.now(timezone.utc) - timedelta(hours=1)
    )


@pytest.fixture
def sample_pull_requests():
    return [
        PullRequest(
            id="1",
            number=101,
            status="open",
            repository="test/repo",
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            raw_data={"title": "Test PR 1"}
        ),
        PullRequest(
            id="2",
            number=102,
            status="closed",
            repository="test/repo",
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            raw_data={"title": "Test PR 2"}
        )
    ]


@pytest.fixture
def service(mock_sync_state_repo, mock_github_client, mock_pr_repo):
    return SyncPullRequestsService(
        mock_sync_state_repo,
        mock_github_client,
        mock_pr_repo
    )


@pytest.mark.asyncio
async def test_sync_repositories(
        service,
        mock_sync_state_repo,
        mock_github_client,
        mock_pr_repo,
        sample_sync_state,
        sample_pull_requests
):
    # Setup
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.return_value = [
        sample_sync_state
    ]
    mock_github_client.get_pull_requests.return_value = sample_pull_requests

    # Execute
    await service.sync_repositories()

    # Verify
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.assert_called_once()
    mock_github_client.get_pull_requests.assert_called_once_with(
        str(sample_sync_state.repository_id),
        since_pr=sample_sync_state.last_synced_pr - 1
    )
    mock_pr_repo.save_batch.assert_called_once_with(sample_pull_requests)
    mock_sync_state_repo.save.assert_called_once()


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
    mock_github_client.get_pull_requests.side_effect = Exception("API Error")

    # Execute
    await service.sync_repositories()

    # Verify service continues despite error
    mock_sync_state_repo.find_outdated_repositories_ready_to_sync.assert_called_once()
    mock_github_client.get_pull_requests.assert_called_once()
