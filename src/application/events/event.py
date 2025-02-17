from abc import ABC
from datetime import datetime


class Event(ABC):
    """Clase base para eventos."""

    def __init__(self):
        self.occurred_on = datetime.utcnow()