from abc import ABC, abstractmethod
from datetime import datetime

from app.models.enums import AttackPhase, Severity


# abstract class
class SecurityEvent(ABC):
    counter = 0

    def __init__(self, timestamp: datetime, host: str, description: str = "",
                 severity: Severity = Severity.MEDIUM) -> None:
        SecurityEvent.counter += 1
        self.event_id = f"EVT-{SecurityEvent.counter:04d}"
        self.timestamp = timestamp
        self.host = host
        self.description = description
        self.severity = severity
        self.previous_event: SecurityEvent | None = None
        self.next_event: SecurityEvent | None = None

    @abstractmethod
    def phase(self) -> AttackPhase:
        pass

    @abstractmethod
    def indicators(self) -> dict:
        pass

    @abstractmethod
    def summary(self) -> str:
        pass

    def to_dict(self) -> dict:
        phase = self.phase()
        return {
            "id": self.event_id,
            "type": type(self).__name__,
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "host": self.host,
            "description": self.description,
            "severity": self.severity.name,
            "summary": self.summary(),
            "indicators": self.indicators(),
            "phase": {
                "name": phase.name,
                "label": phase.label,
                "tactic": phase.tactic_id,
                "color": phase.color,
            },
        }
