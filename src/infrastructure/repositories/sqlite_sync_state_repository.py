import sqlite3
import json
from datetime import datetime, timedelta
import asyncio
from typing import List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ...domain.entities.sync_state import SyncState
from ...application.interfaces.sync_state_repository import SyncStateRepository
from ...domain.value_objects.sync_state import RepositoryId, ProviderType, RateLimit


class SQLiteSyncStateRepository(SyncStateRepository):


    def __init__(self, db_path: str):
        """
        Initialize SQLite repository
        :param db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=1)

        # Initialize database
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_states (
                    repository_owner TEXT NOT NULL,
                    repository_name TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    last_synced_pr INTEGER NOT NULL,
                    rate_limit_reset TIMESTAMP,
                    synchronized BOOLEAN NOT NULL DEFAULT 0,
                    last_sync_time TIMESTAMP,
                    PRIMARY KEY (repository_owner, repository_name, provider_type)
                )
            """)

            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS last_sync_time 
                ON sync_states(last_sync_time)
            """)

            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()

    async def save(self, state: SyncState) -> None:
        def _save():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sync_states 
                    (repository_owner, repository_name, provider_type, last_synced_pr,
                     rate_limit_reset, synchronized, last_sync_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    state.repository_id.owner,
                    state.repository_id.name,
                    state.repository_id.provider.value,
                    state.last_synced_pr,
                    state.rate_limit.reset_time.isoformat() if state.rate_limit else None,
                    state.synchronized,
                    state.last_sync_time.isoformat() if state.last_sync_time else None
                ))

        await asyncio.get_event_loop().run_in_executor(self.executor, _save)

    async def get(self, repository_id: str, provider_type: str) -> Optional[SyncState]:
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                owner, name = repository_id.split('/')
                cursor = conn.execute("""
                    SELECT * FROM sync_states 
                    WHERE repository_owner = ? 
                    AND repository_name = ? 
                    AND provider_type = ?
                """, (owner, name, provider_type.lower()))

                row = cursor.fetchone()
                return self._row_to_sync_state(row) if row else None

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    async def find_outdated_repositories_ready_to_sync(self, _from: datetime) -> List[SyncState]:
        """Get sync state for all repositories that have to be sync, This means sync activated and rate limit not exceeded"""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM sync_states 
                    WHERE synchronized = 1 AND (rate_limit_reset is null OR rate_limit_reset <= ?) AND (last_sync_time is null OR last_sync_time <= ?) 
                    """,
                    (_from.isoformat(), (_from - timedelta(hours=6)).isoformat()),
                )

                return [self._row_to_sync_state(row) for row in cursor.fetchall()]

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    def _row_to_sync_state(self, row: sqlite3.Row) -> SyncState:
        """Convert a database row to a SyncState entity"""
        repository_id = RepositoryId(
            owner=row['repository_owner'],
            name=row['repository_name'],
            provider=ProviderType(row['provider_type'])
        )

        rate_limit = None
        if row['rate_limit_reset']:
            rate_limit = RateLimit(
                reset_time=datetime.fromisoformat(row['rate_limit_reset'])
            )

        return SyncState(
            repository_id=repository_id,
            last_synced_pr=row['last_synced_pr'],
            rate_limit=rate_limit,
            synchronized=bool(row['synchronized']),
            last_sync_time=datetime.fromisoformat(row['last_sync_time'])
            if row['last_sync_time'] else None
        )

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass