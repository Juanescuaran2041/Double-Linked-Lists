from app.models import AttackPhase, AttackTimeline, EventFactory, SecurityEvent
from app.services.forensic_investigator import ForensicInvestigator


class IncidentCase:

    def __init__(self, title: str) -> None:
        self.title = title
        self.timeline = AttackTimeline()
        self.investigator = ForensicInvestigator(self.timeline)

    def clear(self) -> None:
        self.timeline.clear()
        self.investigator.current = None

    def get_event(self, event_id: str) -> SecurityEvent:
        event = self.timeline.find_event(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        return event

    def add_evidence(self, data: dict) -> SecurityEvent:
        event = EventFactory.create(data)
        self.timeline.add_event(event)
        self.investigator.current = event
        return event

    def remove_evidence(self, event_id: str) -> SecurityEvent:
        event = self.get_event(event_id)
        self.investigator.release(event)
        return self.timeline.remove_event(event)

    def move_evidence(self, event_id: str, before_id: str | None) -> None:
        event = self.get_event(event_id)
        if before_id is None:
            self.timeline.move_event_to_end(event)
        else:
            reference = self.get_event(before_id)
            self.timeline.move_event_before(event, reference)
        self.investigator.current = event

    def snapshot(self) -> dict:
        events = []
        for event in self.timeline:
            item = event.to_dict()
            item["prev_id"] = None
            item["next_id"] = None
            item["out_of_order"] = False

            if event.previous_event is not None:
                item["prev_id"] = event.previous_event.event_id
                if event.previous_event.timestamp > event.timestamp:
                    item["out_of_order"] = True
            if event.next_event is not None:
                item["next_id"] = event.next_event.event_id

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

        cursor = None
        if self.investigator.current is not None:
            cursor = self.investigator.current.event_id

        return {
            "title": self.title,
            "size": len(self.timeline),
            "cursor": cursor,
            "events": events,
            "backward": backward,
            "is_empty": self.timeline.is_empty(),
            "stats": self.timeline.phase_stats(),
            "phases": phases,
            "event_types": EventFactory.fields(),
        }
