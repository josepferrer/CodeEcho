import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from .base_service import BaseService
from ..events.event_bus import EventBus
from ..interfaces.progress_reporter import ProgressReporter, ProgressState
from ...application.interfaces.github_client import GitHubClient
from ...application.interfaces.pull_request_repository import PullRequestRepository
from ...application.interfaces.sync_state_repository import SyncStateRepository
from ...domain.entities.sync_state import SyncState
from ...domain.events.pull_request_synced import PullRequestSynced
from ...domain.exceptions.github_exceptions import GitHubRateLimitException, GitHubNotFoundException

logger = logging.getLogger(__name__)


class SyncPullRequestsService(BaseService):
    def __init__(
            self,
            sync_state_repository: SyncStateRepository,
            github_client: GitHubClient,
            pull_request_repository: PullRequestRepository,
            event_bus: EventBus,
            progress_reporter: Optional[ProgressReporter] = None
    ):
        super().__init__(event_bus)
        self.sync_state_repository = sync_state_repository
        self.github_client = github_client
        self.pull_request_repository = pull_request_repository
        self._progress_reporter = progress_reporter

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
        last_pull_request = await self.github_client.get_last_pull_request_number(str(sync_state.repository_id))
        while last_pull_request.number >= sync_state.last_synced_pr:
            try:
                pull_request = await self.get_remote_pull_request(sync_state)

                if pull_request:
                    await self.store_new_sync_states(pull_request, sync_state)
                    pr_synced_event = PullRequestSynced(
                        id=pull_request.id,
                        number=pull_request.number,
                        status=pull_request.status,
                        raw_data=pull_request.raw_data,
                        repository=pull_request.repository
                    )
                    await self._event_bus.publish(pr_synced_event)
                    if self._progress_reporter:
                        self._progress_reporter.report_progress(ProgressState(
                            repository=pull_request.repository,
                            current=pull_request.number,
                            total=last_pull_request.number,
                            message=f"Syncing PR #{pull_request.number} repo {pull_request.repository}"
                        ))
            except GitHubRateLimitException as e_rate_limit:  # TODO: This exception shouldn't be Github specific one
                logger.warning(f"Rate limit")
                await self.store_rate_limit_exceeded_state(e_rate_limit, sync_state)
                break
            except GitHubNotFoundException as e:
                logger.info(f"Pull request number {sync_state.last_synced_pr} not exist in repository {sync_state.repository_id}")
                sync_state.next_pull_request(datetime.now(timezone.utc))
            except Exception as e:
                logger.error(f" {sync_state.repository_id}", exc_info=True)
                break

    async def store_rate_limit_exceeded_state(self, e_rate_limit, sync_state):
        sync_state.update_rate_limit(e_rate_limit.reset_time)
        await self.sync_state_repository.save(sync_state)

    async def store_new_sync_states(self, pull_request, sync_state):
        now = datetime.now(timezone.utc)
        sync_state.next_pull_request(now)
        await self.pull_request_repository.save(pull_request)
        await self.sync_state_repository.save(sync_state)

    async def get_remote_pull_request(self, sync_state):
        pull_request = await self.github_client.get_pull_request(
            str(sync_state.repository_id),
            sync_state.get_next_pull_request()
        )
        return pull_request
