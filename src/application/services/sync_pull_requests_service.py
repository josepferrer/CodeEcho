import logging
from datetime import datetime, timezone

from ...application.interfaces.github_client import GitHubClient
from ...application.interfaces.pull_request_repository import PullRequestRepository
from ...application.interfaces.sync_state_repository import SyncStateRepository
from ...domain.entities.sync_state import SyncState
from ...domain.exceptions.github_exceptions import GitHubRateLimitException, GitHubNotFoundException

logger = logging.getLogger(__name__)


class SyncPullRequestsService:
    def __init__(
            self,
            sync_state_repository: SyncStateRepository,
            github_client: GitHubClient,
            pull_request_repository: PullRequestRepository
    ):
        self.sync_state_repository = sync_state_repository
        self.github_client = github_client
        self.pull_request_repository = pull_request_repository

    async def sync_repositories(self) -> None:
        """
        Main synchronization flow:
        1. Find repositories ready to sync
        2. For each repository, sync pull requests
        3. Update sync state
        """
        try:
            now = datetime.now(timezone.utc)
            repositories = await self.sync_state_repository.find_outdated_repositories_ready_to_sync(now)

            for repo_state in repositories:
                logger.info(f"Starting synchronization of  {repo_state}")
                try:
                    await self._sync_repository(repo_state)
                    logger.info(f"Successfully ended synchronization of  {repo_state}")
                except Exception as e:
                    logger.error(f"Error syncing repository {repo_state.repository_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error in sync process: {e}")
            raise

    async def _sync_repository(self, sync_state: SyncState) -> None:
        """Synchronize pull requests for a specific repository"""
        now = datetime.now(timezone.utc)

        while True:
            try:
                pull_request = await self.get_remote_pull_request(now, sync_state)

                if pull_request:
                    await self.store_new_sync_states(pull_request, sync_state)
            except GitHubRateLimitException as e_rate_limit:  # This exception shouldn't be Github specific one
                logger.warning(f"Rate limit")
                await self.store_rate_limit_exceeded_state(e_rate_limit, sync_state)
                break
            except GitHubNotFoundException as e:
                logger.info(f"No more info on remote repository {sync_state.repository_id}")
                break

    async def store_rate_limit_exceeded_state(self, e_rate_limit, sync_state):
        sync_state.update_rate_limit(e_rate_limit.reset_time)
        await self.sync_state_repository.save(sync_state)

    async def store_new_sync_states(self, pull_request, sync_state):
        await self.pull_request_repository.save(pull_request)
        await self.sync_state_repository.save(sync_state)

    async def get_remote_pull_request(self, now, sync_state):
        pull_request = await self.github_client.get_pull_request(
            str(sync_state.repository_id),
            sync_state.next_pull_request(now)
        )
        return pull_request
