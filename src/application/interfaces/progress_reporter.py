from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressState:
    """Value object for progress state"""
    repository: str
    current: int
    total: int
    message: str


class ProgressReporter(ABC):
    """Interface for reporting progress"""

    @abstractmethod
    def report_progress(self, progress: ProgressState) -> None:
        """Report progress update"""
        pass