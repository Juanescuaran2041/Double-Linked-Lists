from abc import ABC, abstractmethod
from datetime import datetime
from itertools import count
from typing import Any, Dict, Optional

from app.models.enums import AttackPhase, Severity

# abstract class
class SecurityEvent(ABC):
    _id_sequence = count(1)

    def __init__(self, timestamp: datetime, host: str, description: str = "",
                 severity: Severity = Severity.MEDIUM) -> None:
        self.event_id = f"EVT-{next(SecurityEvent._id_sequence):04d}"
        self.timestamp = timestamp
        self.host = host
        self.description = description
        self.severity = severity
        # links of the doubly linked list (managed by AttackTimeline)
        self.previous_event: Optional["SecurityEvent"] = None
        self.next_event: Optional["SecurityEvent"] = None

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
