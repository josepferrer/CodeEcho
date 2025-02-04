import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from .sqlite_base_repository import SQLiteBaseRepository
from .sqlite_config import SQLiteConfig
from ...application.interfaces.pull_request_repository import PullRequestRepository
from ...domain.entities.pull_request import PullRequest


class SQLitePullRequestRepository(SQLiteBaseRepository, PullRequestRepository):

    def __init__(self, config: SQLiteConfig):
        super().__init__(config)
        self._mapper = SQLitePullRequestMapper()


    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create the pull requests table schema"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pull_requests (
                    id TEXT PRIMARY KEY,
                    number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    _modified_at TIMESTAMP NOT NULL,
                    UNIQUE(repository, number)
                )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_repository_status 
            ON pull_requests(repository, status)
        """)

    async def save(self, pull_request: PullRequest) -> None:
        """Save or update a single pull request"""
        await self.save_batch([pull_request])

    async def save_batch(self, pull_requests: List[PullRequest]) -> None:
        """Save or update multiple pull requests"""
        if not pull_requests:
            return

        def _save():
            with self._get_connection() as conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO pull_requests 
                    (id, number, status, repository, raw_data, _modified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [to_row(pr) for pr in pull_requests]
                )

        await self._execute_async(_save)

    async def get_open_pull_requests(self, repository: str) -> List[PullRequest]:
        """Get all open pull requests for a repository"""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM pull_requests 
                    WHERE repository = ? AND status = 'open'
                    ORDER BY number DESC
                    """,
                    (repository,)
                )
                return [self._mapper.to_entity(row) for row in cursor.fetchall()]

        return await self._execute_async(_get)

    async def get_by_id(self, pr_id: str) -> Optional[PullRequest]:
        """Get a pull request by its ID"""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM pull_requests WHERE id = ?",
                    (pr_id,)
                )
                row = cursor.fetchone()
                return self._mapper.to_entity(row) if row else None

        return await self._execute_async(_get)

    async def get_by_repo_and_number(self, repository: str, number: int) -> Optional[PullRequest]:
        """Get a pull request by repository and number"""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM pull_requests 
                    WHERE repository = ? AND number = ?
                    """,
                    (repository, number)
                )
                row = cursor.fetchone()
                return self._mapper.to_entity(row) if row else None

        return await self._execute_async(_get)

    async def get_all(self) -> List[PullRequest]:
        """Get all pull requests"""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM pull_requests")
                return [self._mapper.to_entity(row) for row in cursor.fetchall()]

        return await self._execute_async(_get)


class SQLitePullRequestMapper:
    """Dedicated mapper class for converting between domain and persistence models"""

    @staticmethod
    def to_entity(row: sqlite3.Row) -> PullRequest:
        """Convert a database row to a PullRequest entity"""
        return PullRequest(
            id=row['id'],
            number=row['number'],
            status=row['status'],
            repository=row['repository'],
            raw_data=json.loads(row['raw_data'])
        )


def to_row(entity: PullRequest) -> tuple:
    """Convert a PullRequest entity to a database row"""
    return (
        entity.id,
        entity.number,
        entity.status,
        entity.repository,
        json.dumps(entity.raw_data),
        datetime.now(timezone.utc)
    )