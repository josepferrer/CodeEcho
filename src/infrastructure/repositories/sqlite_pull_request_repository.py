import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...application.interfaces.pull_request_repository import PullRequestRepository
from ...domain.entities.pull_request import PullRequest


class SQLitePullRequestRepository(PullRequestRepository):
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
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
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

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_repository_status 
                ON pull_requests(repository, status)
            """)

            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()

    async def save(self, pull_request: PullRequest) -> None:
        """Save or update a single pull request"""
        await self.save_batch([pull_request])

    async def save_batch(self, pull_requests: List[PullRequest]) -> None:
        """Save or update multiple pull requests"""
        if not pull_requests:
            return

        def _save():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prepare the data
                data = [
                    (
                        pr.id,
                        pr.number,
                        pr.status,
                        pr.repository,
                        json.dumps(pr.raw_data),
                        datetime.utcnow().isoformat()
                    )
                    for pr in pull_requests
                ]

                # Use UPSERT (INSERT OR REPLACE)
                cursor.executemany("""
                    INSERT OR REPLACE INTO pull_requests 
                    (id, number, status, repository, raw_data, _modified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, data)

                conn.commit()

        await asyncio.get_event_loop().run_in_executor(self.executor, _save)

    async def get_open_pull_requests(self, repository: str) -> List[PullRequest]:
        """Get all open pull requests for a repository"""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM pull_requests 
                    WHERE repository = ? AND status = 'open'
                    ORDER BY number DESC
                """, (repository,))

                return [self._row_to_pull_request(row) for row in cursor.fetchall()]

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    async def get_by_id(self, pr_id: str) -> Optional[PullRequest]:
        """Get a pull request by its ID"""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM pull_requests WHERE id = ?", (pr_id,))
                row = cursor.fetchone()

                return self._row_to_pull_request(row) if row else None

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    async def get_by_repo_and_number(self, repository: str, number: int) -> Optional[PullRequest]:
        """Get a pull request by repository and number"""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM pull_requests 
                    WHERE repository = ? AND number = ?
                """, (repository, number))

                row = cursor.fetchone()
                return self._row_to_pull_request(row) if row else None

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    async def get_all(self) -> list[PullRequest]:
        """Get a pull request by repository and number"""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM pull_requests 
                """)

                return [self._row_to_pull_request(row) for row in cursor.fetchall()]

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    def _row_to_pull_request(self, row: sqlite3.Row) -> PullRequest:
        """Convert a database row to a PullRequest entity"""
        return PullRequest(
            id=row['id'],
            number=row['number'],
            status=row['status'],
            repository=row['repository'],
            raw_data=json.loads(row['raw_data'])
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
