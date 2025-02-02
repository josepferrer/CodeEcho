import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.presentation.cli.create_sync_state import create_sync_state


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    try:
        Path(db_path).unlink(missing_ok=True)
        Path(f"{db_path}-wal").unlink(missing_ok=True)
        Path(f"{db_path}-shm").unlink(missing_ok=True)
    except:
        pass


def test_create_sync_state_success(temp_db):
    runner = CliRunner()
    result = runner.invoke(create_sync_state, [
        'owner/repo',
        '--db-path', temp_db
    ])

    assert result.exit_code == 0
    assert "created successfully" in result.output


def test_create_sync_state_invalid_repository(temp_db):
    runner = CliRunner()
    result = runner.invoke(create_sync_state, [
        'invalid-repo',
        '--db-path', temp_db
    ])

    assert result.exit_code != 0
    assert "must be in format" in result.output
