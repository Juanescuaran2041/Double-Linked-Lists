from abc import ABC, abstractmethod
from datetime import datetime
from itertools import count
from typing import Any, Dict

from app.models.enums import AttackPhase, Severity

# abstract class
class SecurityEvent(ABC):
    _id_sequence = count(1)

    def __init__(self, timestamp: datetime, host: str, description: str, severity: Severity = Severity.MEDIUM,) -> None:
        self._event_id = f"EVT-{next(SecurityEvent._id_sequence):04d}"
        self._timestamp = timestamp
        self._host = host.strip()
        self._description = description.strip()
        self._severity = severity

    
    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def host(self) -> str:
        return self._host

    @property
    def description(self) -> str:
        return self._description

    @property
    def severity(self) -> Severity:
        return self._severity
    
    @property
    @abstractmethod
    def phase(self) -> AttackPhase:
        pass

    @abstractmethod
    def indicators(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def summary(self) -> str:
        pass

    def to_dict(self) -> Dict[str, Any]:
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
                "name": self.phase.name,
                "label": self.phase.label,
                "tactic": self.phase.tactic_id,
                "color": self.phase.color,
                "order": self.phase.order,
            },
        }

