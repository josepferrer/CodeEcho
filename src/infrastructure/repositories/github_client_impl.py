import aiohttp
from typing import List, Optional, Dict
from datetime import datetime
from ...domain.entities.pull_request import PullRequest
from ...domain.exceptions.github_exceptions import *
from ...application.interfaces.github_client import GitHubClient


class GitHubClientImpl(GitHubClient):
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
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
            raise GitHubAccessError("Repository or pull request not found")
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
            raw_data=data,
            last_updated=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        )