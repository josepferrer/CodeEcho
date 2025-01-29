from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class PullRequest(BaseModel):
    id: str
    number: int
    status: str
    raw_data: Dict
    repository: str
    last_updated: datetime
    created_at: datetime

    class Config:
        frozen = True  # Immutable

    @property
    def is_finished(self) -> bool:
        return self.status in ['closed', 'merged']