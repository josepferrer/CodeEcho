import asyncio
import logging

import click

from src.infrastructure.config.application_config import ApplicationConfig
from src.infrastructure.config.dependency_container import DependencyContainer
from src.infrastructure.repositories.github_client_impl import GitHubClientImpl
from ...application.services.sync_pull_requests_service import SyncPullRequestsService
from ...infrastructure.repositories.sqlite_pull_request_repository import SQLitePullRequestRepository
from ...infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--db-path',
    type=click.Path(exists=True),
    help='Path to the SQLite database'
)
@click.option('--github-token', envvar='GITHUB_TOKEN', required=True, help='GitHub API token')
def sync_pull_requests(db_path: str, github_token: str):
    """Synchronize pull requests from configured repositories"""
    try:

        # Initialize components
        config = ApplicationConfig(github_token=github_token ,base_data=db_path)
        container = DependencyContainer(config)
        service = container.sync_service

        # Run sync
        logger.info("Starting pull requests synchronization...")
        asyncio.run(service.sync_repositories())
        logger.info("Synchronization completed successfully")

    except Exception as e:
        logger.error(f"Error during synchronization: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    sync_pull_requests()
