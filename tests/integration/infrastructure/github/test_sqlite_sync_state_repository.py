import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.domain.entities.sync_state import SyncState
from src.infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup after test
    try:
        Path(temp_path).unlink(missing_ok=True)
        Path(f"{temp_path}-wal").unlink(missing_ok=True)
        Path(f"{temp_path}-shm").unlink(missing_ok=True)
    except:
        pass


@pytest.fixture
def sample_sync_state():
    """Create a sample sync state"""
    return SyncState.create_initial("test/repo", "github")


@pytest.fixture
def sample_sync_state_rate_limit_exceeded():
    """Create a sample sync state"""
    sync_state = SyncState.create_initial("test/repo_rate_limit_exceeded", "github")
    sync_state.update_rate_limit(datetime.now(timezone.utc) + timedelta(hours=24))
    return sync_state


@pytest.fixture
def sample_sync_state_updated():
    """Create a sample sync state"""
    sync_state = SyncState.create_initial("test/repo_updated", "github")
    sync_state.next_pull_request(datetime.now(timezone.utc))
    return sync_state


@pytest.fixture
async def repository(temp_db_path):
    """Create and initialize repository"""
    repo = SQLiteSyncStateRepository(temp_db_path)
    yield repo
    repo.cleanup()


@pytest.mark.asyncio
async def test_save_and_retrieve_state(repository, sample_sync_state):
    """Test saving and retrieving sync state"""
    # Save state
    await repository.save(sample_sync_state)

    # Retrieve state
    retrieved_state = await repository.get(
        f"{sample_sync_state.repository_id.owner}/{sample_sync_state.repository_id.name}",
        sample_sync_state.repository_id.provider.value
    )

    assert retrieved_state is not None
    assert retrieved_state.repository_id == sample_sync_state.repository_id
    assert retrieved_state.last_synced_pr == sample_sync_state.last_synced_pr
    assert retrieved_state.synchronized == sample_sync_state.synchronized


@pytest.mark.asyncio
async def test_find_outdated_repositories_ready_to_sync(repository, sample_sync_state,
                                                        sample_sync_state_rate_limit_exceeded,
                                                        sample_sync_state_updated):
    """Test choosing the right repositories to be synchronized"""
    await repository.save(sample_sync_state)
    await repository.save(sample_sync_state_rate_limit_exceeded)
    await repository.save(sample_sync_state_updated)
    now = datetime.now(timezone.utc)

    outdated_repositories = await repository.find_outdated_repositories_ready_to_sync(now)

    assert outdated_repositories is not None
    assert len(outdated_repositories) == 1
    assert outdated_repositories[0].repository_id == sample_sync_state.repository_id
