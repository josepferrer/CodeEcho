from unittest.mock import AsyncMock

import pytest

from src.domain.entities.sync_state import SyncState


@pytest.fixture
def mock_sync_state_repository():
    repository = AsyncMock()
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()
    return repository


@pytest.fixture
def service(mock_sync_state_repository):
    return SyncStateService(mock_sync_state_repository)


@pytest.mark.asyncio
async def test_create_sync_state_success(service, mock_sync_state_repository):
    # Arrange
    request = CreateSyncStateRequest(
        repository_id="owner/repo",
        provider_type="github",
        synchronized=True
    )

    # Act
    result = await service.execute(request)

    # Assert
    assert isinstance(result, SyncState)
    assert str(result.repository_id) == "owner/repo"
    assert result.repository_id.provider.value == "github"
    assert result.synchronized == True
    mock_sync_state_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_sync_state_already_exists(service, mock_sync_state_repository):
    # Arrange
    mock_sync_state_repository.get.return_value = SyncState.create_initial(
        "owner/repo",
        "github"
    )

    request = CreateSyncStateRequest(
        repository_id="owner/repo",
        provider_type="github",
        synchronized=True
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Repository .* is already configured"):
        await service.execute(request)


@pytest.mark.asyncio
async def test_create_sync_state_disabled_sync(service, mock_sync_state_repository):
    # Arrange
    request = CreateSyncStateRequest(
        repository_id="owner/repo",
        provider_type="github",
        synchronized=False
    )

    # Act
    result = await service.execute(request)

    # Assert
    assert not result.synchronized
    mock_sync_state_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_list_sync_states(service, mock_sync_state_repository):
    # Arrange
    mock_states = [
        SyncState.create_initial("owner/repo1", "github"),
        SyncState.create_initial("owner/repo2", "gitlab")
    ]
    mock_sync_state_repository.get_all.return_value = mock_states

    # Act
    result = await service.list_all()

    # Assert
    assert len(result) == 2
    assert result[0].repository_id == "owner/repo1"
    assert result[1].repository_id == "owner/repo2"
    mock_sync_state_repository.get_all.assert_called_once()
