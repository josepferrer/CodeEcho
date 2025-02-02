import asyncio
import logging
from pathlib import Path

import click

from ...application.dto.sync_state_dto import CreateSyncStateRequest
from ...application.services.sync_state_service import SyncStateService
from ...infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository

logger = logging.getLogger(__name__)


@click.command()
@click.argument('repository', type=str)
@click.option(
    '--provider',
    type=click.Choice(['github', 'gitlab'], case_sensitive=False),
    default='github',
    help='Version control provider'
)
@click.option(
    '--sync/--no-sync',
    default=True,
    help='Enable or disable synchronization'
)
@click.option(
    '--db-path',
    type=click.Path(),
    default='data/sync.db',
    help='Path to the SQLite database'
)
def create_sync_state(
        repository: str,
        provider: str,
        sync: bool,
        db_path: str
):
    """
    Create a new sync state for a repository.

    REPOSITORY should be in the format "owner/repo"
    """
    try:
        # Validate repository format
        if '/' not in repository:
            raise click.BadParameter(
                'Repository must be in format "owner/repo"'
            )

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize components
        sync_repo = SQLiteSyncStateRepository(db_path)
        service = SyncStateService(sync_repo)

        # Create request
        request = CreateSyncStateRequest(
            repository_id=repository,
            provider_type=provider.lower(),
            synchronized=sync
        )

        # Execute service
        logger.info(f"Creating sync state for {repository}...")
        sync_state = asyncio.run(service.create(request))

        logger.info(
            f"Sync state created successfully for {repository}. "
            f"Synchronization is {'enabled' if sync else 'disabled'}."
        )

    except ValueError as e:
        logger.error(f"Error creating sync state: {e}")
        raise click.ClickException(str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    create_sync_state()
