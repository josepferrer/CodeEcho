import tempfile
from pathlib import Path

import pytest

from src.domain.entities.pull_request import PullRequest
from src.infrastructure.repositories.sqlite_config import SQLiteConfig
from src.infrastructure.repositories.sqlite_pull_request_repository import SQLitePullRequestRepository


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup after test
    try:
        Path(temp_path).unlink(missing_ok=True)
        Path(f"{temp_path}-wal").unlink(missing_ok=True)  # Remove WAL file
        Path(f"{temp_path}-shm").unlink(missing_ok=True)  # Remove SHM file
    except:
        pass


@pytest.fixture
def sample_pr():
    """Create a sample pull request"""
    return PullRequest(
        id="111",
        number=1,
        status="open",
        repository="test/repo",
        raw_data={
            "title": "Test PR",
            "body": "Test body",
            "user": {"login": "testuser"}
        }
    )


@pytest.fixture
async def repository(temp_db_path):
    """Create and initialize repository"""
    config = SQLiteConfig.create(
        db_path=Path(temp_db_path),
        journal_mode="WAL",
        foreign_keys=True,
        max_workers=1
    )
    repo = SQLitePullRequestRepository(config)
    yield repo
    repo.cleanup()


@pytest.mark.asyncio
async def test_save_and_retrieve_pr(repository, sample_pr):
    """Test saving and retrieving a pull request"""
    # Save PR
    await repository.save(sample_pr)

    # Retrieve by ID
    retrieved_pr = await repository.get_by_id(sample_pr.id)

    assert retrieved_pr is not None
    assert retrieved_pr.id == sample_pr.id
    assert retrieved_pr.number == sample_pr.number
    assert retrieved_pr.status == sample_pr.status
    assert retrieved_pr.raw_data["title"] == "Test PR"


@pytest.mark.asyncio
async def test_batch_save(repository):
    """Test batch saving of pull requests"""
    # Create multiple PRs
    prs = [
        PullRequest(
            id=f"12{i}",
            number=i,
            status="open",
            repository="test/repo",
            raw_data={"title": f"PR {i}"}
        )
        for i in range(1, 4)
    ]

    # Save batch
    await repository.save_batch(prs)

    # Verify all were saved
    for pr in prs:
        retrieved = await repository.get_by_id(pr.id)
        assert retrieved is not None
        assert retrieved.id == pr.id


@pytest.mark.asyncio
async def test_updated_pr(repository, sample_pr):
    """Test filtering open pull requests"""
    # Save an open PR
    await repository.save(sample_pr)
    # Save a closed PR
    open_pr = PullRequest(
        id="123",
        number=77,
        status="open",
        repository="test/repo",
        raw_data={"title": "Closed PR"}
    )
    closed_pr = PullRequest(
        id="124",
        number=77,
        status="closed",
        repository="test/repo",
        raw_data={"title": "Closed PR"}
    )
    await repository.save(open_pr)
    await repository.save(closed_pr)

    # Get open PRs
    retrieved_prs = await repository.get_by_repo_and_number("test/repo", 77)
    assert retrieved_prs.id == closed_pr.id
    assert retrieved_prs.id != open_pr.id
    assert retrieved_prs.status == closed_pr.status


@pytest.mark.asyncio
async def test_get_open_prs(repository, sample_pr):
    """Test filtering open pull requests"""
    # Save an open PR
    await repository.save(sample_pr)
    # Save a closed PR
    closed_pr = PullRequest(
        id="123",
        number=2,
        status="close",
        repository="test/repo",
        raw_data={"title": "Closed PR"}
    )
    await repository.save(closed_pr)

    # Get open PRs
    open_prs = await repository.get_open_pull_requests("test/repo")

    assert len(open_prs) == 1
    assert open_prs[0].id == sample_pr.id


@pytest.mark.asyncio
async def test_get_get_by_repo_and_number(repository, sample_pr):
    """Test filtering open pull requests"""
    # Save an open PR
    await repository.save(sample_pr)
    # Save a closed PR
    closed_pr = PullRequest(
        id="124",
        number=77,
        status="closed",
        repository="test/repo",
        raw_data={"title": "Closed PR"}
    )
    await repository.save(closed_pr)

    # Get open PRs
    open_prs = await repository.get_by_repo_and_number("test/repo", 77)
    assert open_prs.id == closed_pr.id
