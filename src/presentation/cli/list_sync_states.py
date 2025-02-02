import asyncio
import logging
from datetime import datetime

import click
from tabulate import tabulate

from ...application.services.sync_state_service import SyncStateService
from ...infrastructure.repositories.sqlite_sync_state_repository import SQLiteSyncStateRepository

logger = logging.getLogger(__name__)


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"


@click.command()
@click.option(
    '--db-path',
    type=click.Path(exists=True),
    default='data/sync.db',
    help='Path to the SQLite database'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format'
)
def list_sync_states(db_path: str, format: str):
    """List all configured repositories for synchronization."""
    try:
        # Initialize components
        sync_repo = SQLiteSyncStateRepository(db_path)
        service = SyncStateService(sync_repo)

        # Get all sync states
        sync_states = asyncio.run(service.list_all())

        if format == 'json':
            # JSON output
            import json
            click.echo(json.dumps([
                {
                    'repository': state.repository_id,
                    'provider': state.provider_type,
                    'last_synced_pr': state.last_synced_pr,
                    'synchronized': state.synchronized,
                    'last_sync_time': format_datetime(state.last_sync_time),
                    'rate_limit_reset': format_datetime(state.rate_limit_reset)
                }
                for state in sync_states
            ], indent=2))
        else:
            # Table output
            if not sync_states:
                click.echo("No repositories configured for synchronization.")
                return

            table_data = [
                [
                    state.repository_id,
                    state.provider_type,
                    state.last_synced_pr,
                    '✓' if state.synchronized else '✗',
                    format_datetime(state.last_sync_time),
                    format_datetime(state.rate_limit_reset)
                ]
                for state in sync_states
            ]

            headers = [
                'Repository',
                'Provider',
                'Last PR',
                'Sync',
                'Last Sync Time',
                'Rate Limit Reset'
            ]

            click.echo(tabulate(
                table_data,
                headers=headers,
                tablefmt='grid'
            ))

    except Exception as e:
        logger.error(f"Error listing sync states: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    list_sync_states()
