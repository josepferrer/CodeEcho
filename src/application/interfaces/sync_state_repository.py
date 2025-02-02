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
        """
        Find repositories that:
        1. Are marked for synchronization
        2. Have no rate limit or rate limit has expired
        3. Haven't been synced recently
        """
        pass

    class SyncStateRepository(ABC):
        @abstractmethod
        async def get_all(self) -> List[SyncState]:
            """Get all sync states"""
            pass
