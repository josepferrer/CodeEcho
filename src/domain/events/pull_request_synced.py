from dataclasses import dataclass
from typing import Dict
from src.application.events.event import Event


@dataclass(frozen=True)
class PullRequestSynced(Event):
    """Event for sync progress updates"""
    id: str
    number: int
    status: str
    raw_data: Dict
    repository: str