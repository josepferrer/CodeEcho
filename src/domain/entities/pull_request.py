from typing import Dict

from pydantic import BaseModel


class PullRequest(BaseModel):
    id: str
    number: int
    status: str
    raw_data: Dict
    repository: str

    @property
    def is_finished(self) -> bool:
        return self.status in ['closed', 'merged']
