import datetime
from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.entities.sync_state import SyncState

class SyncStateRepository(ABC):
    @abstractmethod
    async def save(self, state: SyncState) -> None:
        """Save or update sync state"""
        pass

    @abstractmethod
    async def get(self, repository_id: str, provider_type: str) -> Optional[SyncState]:
        """Get sync state for a specific repository and provider"""
        pass

    @abstractmethod
    async def find_outdated_repositories_ready_to_sync(self, _from: datetime) -> List[SyncState]:
        """Get all repositories that are marked for synchronization"""
        pass