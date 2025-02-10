import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from .sqlite_base_repository import SQLiteBaseRepository
from .sqlite_config import SQLiteConfig
from ...application.interfaces.sync_state_repository import SyncStateRepository
from ...domain.entities.sync_state import SyncState
from ...domain.value_objects.sync_state import RepositoryId, ProviderType, RateLimit


class SQLiteSyncStateRepository(SQLiteBaseRepository, SyncStateRepository):

    def __init__(self, config: SQLiteConfig):
        super().__init__(config)
        self._mapper = SQLiteSyncStateMapper()

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create the sync states table schema"""
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
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_sync_time 
            ON sync_states(last_sync_time)
        """)

    async def save(self, state: SyncState) -> None:
        """Save or update a sync state"""

        def _save():
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sync_states 
                    (repository_owner, repository_name, provider_type, last_synced_pr,
                     rate_limit_reset, synchronized, last_sync_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, self._mapper.to_row(state))

        await self._execute_async(_save)

    async def get(self, repository_id: str, provider_type: str) -> Optional[SyncState]:
        """Get sync state by repository ID and provider type"""

        def _get():
            with self._get_connection() as conn:
                owner, name = repository_id.split('/')
                cursor = conn.execute("""
                    SELECT * FROM sync_states 
                    WHERE repository_owner = ? 
                    AND repository_name = ? 
                    AND provider_type = ?
                """, (owner, name, provider_type.lower()))

                row = cursor.fetchone()
                return self._mapper.to_entity(row) if row else None

        return await self._execute_async(_get)

    async def find_outdated_repositories_ready_to_sync(self, from_date: datetime) -> List[SyncState]:
        """Get sync states for repositories ready to sync"""

        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM sync_states 
                    WHERE synchronized = 1 
                    AND (rate_limit_reset is null OR rate_limit_reset <= ?) 
                    AND (last_sync_time is null OR last_sync_time <= ?)
                    """,
                    (
                        from_date.isoformat(),
                        from_date.isoformat()
                    )
                )
                return [self._mapper.to_entity(row) for row in cursor.fetchall()]

        return await self._execute_async(_get)

    async def get_all(self) -> List[SyncState]:
        """Get all sync states"""

        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM sync_states 
                    ORDER BY repository_owner, repository_name
                """)
                return [self._mapper.to_entity(row) for row in cursor.fetchall()]

        return await self._execute_async(_get)


class SQLiteSyncStateMapper:
    """Dedicated mapper class for converting between domain and persistence models"""

    @staticmethod
    def to_entity(row: sqlite3.Row) -> SyncState:
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

    @staticmethod
    def to_row(entity: SyncState) -> tuple:
        """Convert a SyncState entity to a database row"""
        return (
            entity.repository_id.owner,
            entity.repository_id.name,
            entity.repository_id.provider.value,
            entity.last_synced_pr,
            entity.rate_limit.reset_time.isoformat() if entity.rate_limit else None,
            entity.synchronized,
            entity.last_sync_time.isoformat() if entity.last_sync_time else None
        )
