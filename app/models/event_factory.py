from datetime import datetime

from app.models.enums import Severity
from app.models.events import (
    ExfiltrationEvent,
    LateralMovementEvent,
    MalwareExecutionEvent,
    PhishingEvent,
    PrivilegeEscalationEvent,
    ReconnaissanceEvent,
)
from app.models.security_event import SecurityEvent


class EventFactory:
    # event type -> (class, specific fields asked in the UI form)
    TYPES = {
        "reconnaissance": (ReconnaissanceEvent, ["source_ip", "ports_scanned"]),
        "phishing": (PhishingEvent, ["sender", "subject"]),
        "execution": (MalwareExecutionEvent, ["process", "sha256"]),
        "privilege_escalation": (PrivilegeEscalationEvent, ["account", "technique"]),
        "lateral_movement": (LateralMovementEvent, ["target_host", "protocol"]),
        "exfiltration": (ExfiltrationEvent, ["destination", "size_mb"]),
    }

    @classmethod
    def fields(cls) -> dict:
        return {name: fields for name, (_, fields) in cls.TYPES.items()}

    @classmethod
    def create(cls, data: dict) -> SecurityEvent:
        if data.get("type") not in cls.TYPES:
            raise ValueError("Unknown event type")
        event_class, fields = cls.TYPES[data["type"]]

        missing = [f for f in ["timestamp", "host", *fields] if not data.get(f)]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")

        return event_class(
            datetime.fromisoformat(data["timestamp"]),
            data["host"],
            data.get("description", ""),
            Severity[data.get("severity", "MEDIUM")],
            *[data[f] for f in fields],
        )
