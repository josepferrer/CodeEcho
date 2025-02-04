import sqlite3
import asyncio
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, Callable, TypeVar, Optional

from .sqlite_config import SQLiteConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SQLiteBaseRepository(ABC):
    """
    Base class for SQLite repositories implementing common functionality
    following Clean Architecture principles
    """

    def __init__(self, config: SQLiteConfig):
        """Initialize repository with configuration"""
        self._config = config
        self._executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database with schema and settings"""
        with self._get_connection() as conn:
            self._setup_database(conn)
            self._create_schema(conn)

    @abstractmethod
    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create database schema - to be implemented by child classes"""
        pass

    def _setup_database(self, conn: sqlite3.Connection) -> None:
        """Configure database settings"""
        conn.execute(f"PRAGMA journal_mode={self._config.journal_mode}")
        conn.execute(f"PRAGMA foreign_keys={'ON' if self._config.foreign_keys else 'OFF'}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper configuration"""
        conn = None
        try:
            conn = sqlite3.connect(self._config.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    async def _execute_async(self, operation: Callable[[], T]) -> T:
        """Execute database operation asynchronously"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                self._executor,
                operation
            )
        except sqlite3.Error as e:
            logger.error(f"Database error in async execution: {e}")
            raise

    def cleanup(self) -> None:
        """Cleanup resources"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()