from typing import Dict
from tqdm import tqdm
from src.application.interfaces.progress_reporter import ProgressReporter, ProgressState


class TqdmProgressReporter(ProgressReporter):
    """Progress reporter implementation using tqdm"""

    def __init__(self):
        self._progress_bars: Dict[str, tqdm] = {}

    def report_progress(self, progress: ProgressState) -> None:
        """Handle progress update"""
        if progress.repository not in self._progress_bars:
            self._init_progress_bar(progress)

        self._update_progress(progress)

        if progress.current >= progress.total:
            self._close_progress_bar(progress.repository)

    def _init_progress_bar(self, progress: ProgressState) -> None:
        self._progress_bars[progress.repository] = tqdm(
            total=progress.total,
            desc=f"Syncing {progress.repository}",
            unit="PR"
        )

    def _update_progress(self, progress: ProgressState) -> None:
        if bar := self._progress_bars.get(progress.repository):
            bar.update(1)
            bar.set_description(progress.message)

    def _close_progress_bar(self, repository: str) -> None:
        if bar := self._progress_bars.pop(repository, None):
            bar.close()