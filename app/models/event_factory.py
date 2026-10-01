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
    TYPES = {
        "reconnaissance": (ReconnaissanceEvent, ["source_ip", "ports_scanned"]),
        "phishing": (PhishingEvent, ["sender", "subject"]),
        "execution": (MalwareExecutionEvent, ["process", "sha256"]),
        "privilege_escalation": (PrivilegeEscalationEvent, ["account", "technique"]),
        "lateral_movement": (LateralMovementEvent, ["target_host", "protocol"]),
        "exfiltration": (ExfiltrationEvent, ["destination", "size_mb"]),
    }

    @staticmethod
    def fields() -> dict:
        result = {}
        for name in EventFactory.TYPES:
            result[name] = EventFactory.TYPES[name][1]
        return result

    @staticmethod
    def create(data: dict) -> SecurityEvent:
        event_type = data.get("type")
        if event_type not in EventFactory.TYPES:
            raise ValueError("Unknown event type")

        event_class, fields = EventFactory.TYPES[event_type]
        for field in ["timestamp", "host"] + fields:
            if not data.get(field):
                raise ValueError(f"Missing field: {field}")

        extra_values = [data[field] for field in fields]
        return event_class(
            datetime.fromisoformat(data["timestamp"]),
            data["host"],
            data.get("description", ""),
            Severity[data.get("severity", "MEDIUM")],
            *extra_values,
        )
