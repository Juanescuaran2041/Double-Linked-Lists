
from datetime import datetime
from typing import Any, Dict, Type

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
    
    _REGISTRY: Dict[str, tuple] = {
        "reconnaissance": (ReconnaissanceEvent, ("source_ip", "ports_scanned")),
        "phishing": (PhishingEvent, ("sender", "subject")),
        "execution": (MalwareExecutionEvent, ("process", "sha256")),
        "privilege_escalation": (PrivilegeEscalationEvent, ("account", "technique")),
        "lateral_movement": (LateralMovementEvent, ("target_host", "protocol")),
        "exfiltration": (ExfiltrationEvent, ("destination", "size_mb")),
    }

    @classmethod
    def available_types(cls) -> Dict[str, list]:
        return {key: list(fields) for key, (_, fields) in cls._REGISTRY.items()}

    @classmethod
    def create(cls, event_type: str, payload: Dict[str, Any]) -> SecurityEvent:
        if event_type not in cls._REGISTRY:
            raise ValueError(f"Unknown event type: {event_type}")
        event_class: Type[SecurityEvent]
        event_class, fields = cls._REGISTRY[event_type]

        missing = [f for f in ("timestamp", "host", *fields) if not str(payload.get(f, "")).strip()]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")

        return event_class(
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            host=payload["host"],
            description=payload.get("description", ""),
            severity=Severity.from_name(payload.get("severity", "MEDIUM")),
            **{f: payload[f] for f in fields},
        )
