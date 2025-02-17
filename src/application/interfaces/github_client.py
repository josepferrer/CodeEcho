from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain.entities.pull_request import PullRequest


class GitHubClient(ABC):
    @abstractmethod
    async def get_pull_requests(self, repository: str, page: Optional[int] = 1) -> List[PullRequest]:
        pass

    @abstractmethod
    async def get_pull_request(self, repository: str, number: int) -> PullRequest:
        pass

    @abstractmethod
    async def get_last_pull_request_number(self, repository: str) -> PullRequest:
        pass
