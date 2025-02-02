import logging
from typing import List, Optional, Dict

import aiohttp

from ...application.interfaces.github_client import GitHubClient
from ...domain.entities.pull_request import PullRequest
from ...domain.exceptions.github_exceptions import *

logger = logging.getLogger(__name__)

class GitHubClientImpl(GitHubClient):
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pull_requests(
            self,
            repository: str,
            page: Optional[int] = 1
    ) -> List[PullRequest]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{repository}/pulls"
                params = {"state": "all", "per_page": 100}
                if page:
                    params["page"] = page
                async with session.get(url, headers=self.headers, params=params) as response:
                    self._handle_response_status(response)
                    data = await response.json()
                    return [self._create_pull_request(repository, item) for item in data]

        except aiohttp.ClientError as e:
            raise GitHubConnectionError(f"Connection error: {str(e)}")

    async def get_pull_request(self, repository: str, number: int) -> PullRequest:
        """Get a specific pull request by number"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{repository}/pulls/{number}"
                logging.info(f"GET: {url}")

                async with session.get(url, headers=self.headers) as response:
                    self._handle_response_status(response)
                    data = await response.json()

                    return self._create_pull_request(repository, data)

        except aiohttp.ClientError as e:
            raise GitHubConnectionError(f"Connection error: {str(e)}")

    def _handle_response_status(self, response: aiohttp.ClientResponse) -> None:
        """Handle API response status and raise appropriate exceptions."""
        status = response.status
        ratelimit_remaining = response.headers.get("X-RateLimit-Remaining")
        ratelimit_reset = response.headers.get("X-RateLimit-Reset")

        if status in [403, 429] and ratelimit_remaining == "0":
            reset_time = int(ratelimit_reset) if ratelimit_reset else 0
            raise GitHubRateLimitException(reset_time)
        if status == 401:
            raise GitHubAuthenticationError("Invalid GitHub token")
        elif status == 403:
            raise GitHubAccessError("Access denied to repository")
        elif status == 404:
            raise GitHubNotFoundException("Repository or pull request not found")
        elif status >= 500:
            raise GitHubConnectionError("GitHub service error")
        elif status != 200:
            raise GitHubBaseException(f"GitHub API error: {status}")

    def _create_pull_request(self, repository: str, data: Dict) -> PullRequest:
        return PullRequest(
            id=str(data["id"]),
            number=data["number"],
            status=data["state"],
            repository=repository,
            raw_data=data
        )
