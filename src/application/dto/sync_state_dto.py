from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CreateSyncStateRequest:
    repository_id: str  # Format: "owner/repo"
    provider_type: str  # "github" or "gitlab"
    synchronized: bool


@dataclass
class SyncStateResponse:
    repository_id: str
    provider_type: str
    last_synced_pr: int
    synchronized: bool
    last_sync_time: Optional[datetime]
    rate_limit_reset: Optional[datetime]

    @classmethod
    def from_entity(cls, sync_state):
        return cls(
            repository_id=str(sync_state.repository_id),
            provider_type=sync_state.repository_id.provider.value,
            last_synced_pr=sync_state.last_synced_pr,
            synchronized=sync_state.synchronized,
            last_sync_time=sync_state.last_sync_time,
            rate_limit_reset=sync_state.rate_limit.reset_time if sync_state.rate_limit else None
        )
