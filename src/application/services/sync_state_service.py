from typing import List

from ..dto.sync_state_dto import CreateSyncStateRequest, SyncStateResponse
from ...application.interfaces.sync_state_repository import SyncStateRepository
from ...domain.entities.sync_state import SyncState


class SyncStateService:
    def __init__(self, sync_state_repository: SyncStateRepository):
        self.sync_state_repository = sync_state_repository

    async def create(self, request: CreateSyncStateRequest) -> SyncStateResponse:
        """Create a new SyncState"""
        # Check if repository already exists
        existing_state = await self.sync_state_repository.get(
            request.repository_id,
            request.provider_type
        )

        if existing_state:
            raise ValueError(
                f"Repository {request.repository_id} is already configured "
                f"for {request.provider_type}"
            )

        # Create new sync state
        sync_state = SyncState.create_initial(
            request.repository_id,
            request.provider_type
        )

        # Set synchronization if requested
        if request.synchronized:
            sync_state.toggle_synchronization(True)

        # Save to repository
        await self.sync_state_repository.save(sync_state)

        return SyncStateResponse.from_entity(sync_state)

    async def list_all(self) -> List[SyncStateResponse]:
        """List all sync states"""
        sync_states = await self.sync_state_repository.get_all()
        return [SyncStateResponse.from_entity(state) for state in sync_states]
