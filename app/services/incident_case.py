"""Incident case: facade that the web layer talks to."""

from typing import Any, Dict, List

from app.models import AttackPhase, AttackTimeline, EventFactory, SecurityEvent
from app.services.forensic_investigator import ForensicInvestigator


class IncidentCase:
    """Facade pattern: one entry point for timeline + investigator.

    The case starts EMPTY: every event is added by the analyst from the UI.
    """

    def __init__(self, title: str) -> None:
        self._title = title
        self._timeline = AttackTimeline()
        self._investigator = ForensicInvestigator(self._timeline)

    @property
    def investigator(self) -> ForensicInvestigator:
        return self._investigator

    def clear(self) -> None:
        self._timeline.clear()
        self._investigator.go_to_first()

    def add_evidence(self, data: Dict[str, Any]) -> SecurityEvent:
        event = EventFactory.create(data)
        self._timeline.add_event(event)
        self._investigator.jump_to(event.event_id)
        return event

    def remove_evidence(self, event_id: str) -> SecurityEvent:
        event = self._timeline.find_event(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        self._investigator.release(event)
        return self._timeline.remove_event(event)

    def snapshot(self) -> Dict[str, Any]:
        """Serializable view of the list, including prev/next pointers."""
        chain: List[Dict[str, Any]] = []
        for event in self._timeline:
            item = event.to_dict()
            item["prev_id"] = event.previous_event.event_id if event.previous_event else None
            item["next_id"] = event.next_event.event_id if event.next_event else None
            chain.append(item)

        current = self._investigator.current
        return {
            "title": self._title,
            "size": len(self._timeline),
            "cursor": current.event_id if current else None,
            "events": chain,
            "stats": self._timeline.phase_stats(),
            "phases": [
                {"name": p.name, "label": p.label, "tactic": p.tactic_id, "color": p.color}
                for p in AttackPhase
            ],
            "event_types": EventFactory.fields(),
        }
