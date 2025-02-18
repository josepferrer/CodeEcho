import asyncio
import logging

import click

from src.presentation.cli.base_cli import Cli
from src.presentation.cli.tqdm_progress_reporter import TqdmProgressReporter

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
        container = Cli.service_container(db_path=db_path, github_token=github_token)
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
