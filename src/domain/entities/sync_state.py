from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.sync_state import RepositoryId, RateLimit


@dataclass
class SyncState:
    """Entity representing the synchronization state of a repository"""
    repository_id: RepositoryId
    last_synced_pr: int
    rate_limit: Optional[RateLimit]
    synchronized: bool
    last_sync_time: Optional[datetime]

    @classmethod
    def create_initial(cls, repository_string: str, provider_type: str) -> 'SyncState':
        """Factory method to create initial sync state"""
        return cls(
            repository_id=RepositoryId.from_string(repository_string, provider_type),
            last_synced_pr=1,
            rate_limit=None,
            synchronized=True,
            last_sync_time=None
        )

    def next_pull_request(self, last_update: datetime) -> int:
        """Get next pull request number and update state"""
        if not self.synchronized:
            raise ValueError("Repository is not marked for synchronization")

        if self.rate_limit and self.rate_limit.is_exceeded():
            raise ValueError(f"Rate limit exceeded. Reset at {self.rate_limit.reset_time}")

        self.last_synced_pr += 1
        self.last_sync_time = last_update
        return self.last_synced_pr

    def update_rate_limit(self, reset_time: datetime) -> None:
        """Update rate limit information"""
        self.rate_limit = RateLimit(reset_time=reset_time)

    def toggle_synchronization(self, enabled: bool) -> None:
        """Enable or disable synchronization"""
        self.synchronized = enabled
        if enabled:
            self.last_sync_time = datetime.utcnow()

    def can_sync(self) -> bool:
        """Check if repository can be synchronized"""
        return self.synchronized

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SyncState):
            return NotImplemented
        return self.repository_id == other.repository_id

    def __hash__(self) -> int:
        return hash(self.repository_id)
