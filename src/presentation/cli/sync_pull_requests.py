import asyncio
import logging

import click

from src.infrastructure.repositories.github_client_impl import GitHubClientImpl
from ...application.services.sync_pull_requests_service import SyncPullRequestsService
from ...infrastructure.repositories.sqlite_pull_request_repository import SQLitePullRequestRepository
from ...infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--sync-db', default='data/sync_state.db', help='Sync state database path')
@click.option('--pr-db', default='data/pull_requests.db', help='Pull requests database path')
@click.option('--github-token', envvar='GITHUB_TOKEN', required=True, help='GitHub API token')
def sync_pull_requests(sync_db: str, pr_db: str, github_token: str):
    """Synchronize pull requests from configured repositories"""
    try:
        # Initialize repositories and client
        sync_repo = SQLiteSyncStateRepository(sync_db)
        pr_repo = SQLitePullRequestRepository(pr_db)
        github_client = GitHubClientImpl(github_token)

        # Create service
        service = SyncPullRequestsService(sync_repo, github_client, pr_repo)

        # Run sync
        logger.info("Starting pull requests synchronization...")
        asyncio.run(service.sync_repositories())
        logger.info("Synchronization completed successfully")

    except Exception as e:
        logger.error(f"Error during synchronization: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    sync_pull_requests()
