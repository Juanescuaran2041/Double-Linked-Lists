from app.models import AttackPhase, AttackTimeline, EventFactory, SecurityEvent
from app.services.forensic_investigator import ForensicInvestigator


class IncidentCase:

    def __init__(self, title: str) -> None:
        self.title = title
        self.timeline = AttackTimeline()
        self.investigator = ForensicInvestigator(self.timeline)

    def clear(self) -> None:
        self.timeline.clear()
        self.investigator.go_to_first()

    def add_evidence(self, data: dict) -> SecurityEvent:
        event = EventFactory.create(data)
        self.timeline.add_event(event)
        self.investigator.current = event
        return event

    def remove_evidence(self, event_id: str) -> SecurityEvent:
        event = self.timeline.find_event(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        self.investigator.release(event)
        return self.timeline.remove_event(event)

    def snapshot(self) -> dict:
        events = []
        for event in self.timeline:
            item = event.to_dict()
            item["prev_id"] = event.previous_event.event_id if event.previous_event else None
            item["next_id"] = event.next_event.event_id if event.next_event else None
            events.append(item)

        backward = []
        for event in reversed(self.timeline):
            backward.append(event.event_id)

        phases = []
        for phase in AttackPhase:
            phases.append({
                "name": phase.name,
                "label": phase.label,
                "tactic": phase.tactic_id,
                "color": phase.color,
            })

        current = self.investigator.current
        return {
            "title": self.title,
            "size": len(self.timeline),
            "cursor": current.event_id if current else None,
            "events": events,
            "backward": backward,
            "is_empty": self.timeline.is_empty(),
            "stats": self.timeline.phase_stats(),
            "phases": phases,
            "event_types": EventFactory.fields(),
        }
