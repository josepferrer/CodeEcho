from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain.entities.pull_request import PullRequest


class PullRequestRepository(ABC):
    @abstractmethod
    async def save(self, pull_request: PullRequest) -> None:
        """Save or update a pull request"""
        pass

    @abstractmethod
    async def save_batch(self, pull_requests: List[PullRequest]) -> None:
        """Save or update multiple pull requests"""
        pass

    @abstractmethod
    async def get_open_pull_requests(self, repository: str) -> List[PullRequest]:
        """Get all open pull requests for a repository"""
        pass

    @abstractmethod
    async def get_by_id(self, pr_id: str) -> Optional[PullRequest]:
        """Get a pull request by its ID"""
        pass

    @abstractmethod
    async def get_by_repo_and_number(self, repository: str, number: int) -> Optional[PullRequest]:
        """Get a pull request by repository and number"""
        pass
