from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


@dataclass(frozen=True)
class SQLiteConfig:
    """Value Object for SQLite configuration"""
    db_path: Path
    journal_mode: str = "WAL"
    foreign_keys: bool = True
    max_workers: int = 1

    @classmethod
    def create(cls, db_path: Union[str, Path], **kwargs) -> 'SQLiteConfig':
        path = Path(db_path) if isinstance(db_path, str) else db_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(db_path=path, **kwargs)


@dataclass(frozen=True)
class SQLiteConnection:
    """Value Object for SQLite connection parameters"""
    path: Path
    timeout: float = 30.0
    isolation_level: Optional[str] = None

    def get_uri(self) -> str:
        return f"file:{self.path}?mode=rw"