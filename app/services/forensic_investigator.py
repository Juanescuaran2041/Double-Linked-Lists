from app.models import AttackPhase, AttackTimeline, SecurityEvent


class ForensicInvestigator:

    def __init__(self, timeline: AttackTimeline) -> None:
        self.timeline = timeline
        self.current: SecurityEvent | None = None

    def go_to_first(self) -> None:
        self.current = self.timeline.first_event

    def go_to_last(self) -> None:
        self.current = self.timeline.last_event

    def step_forward(self) -> None:
        if self.current is not None and self.current.next_event is not None:
            self.current = self.current.next_event

    def step_backward(self) -> None:
        if self.current is not None and self.current.previous_event is not None:
            self.current = self.current.previous_event

    def jump_to(self, event_id: str) -> None:
        event = self.timeline.find_event(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        self.current = event

    def release(self, event: SecurityEvent) -> None:
        if self.current is not event:
            return
        if event.next_event is not None:
            self.current = event.next_event
        else:
            self.current = event.previous_event

    def trace_to_patient_zero(self) -> dict:
        path = []
        entry_point = None
        oldest_event = None
        event = self.current
        while event is not None:
            path.append(event.event_id)
            if event.phase() == AttackPhase.INITIAL_ACCESS:
                entry_point = event
            oldest_event = event
            event = event.previous_event

        patient_zero = entry_point or oldest_event
        return {
            "path": path,
            "patient_zero": patient_zero.to_dict() if patient_zero else None,
        }

    def trace_impact(self) -> dict:
        path = []
        hosts = []
        exfiltrated_mb = 0
        event = self.current
        while event is not None:
            path.append(event.event_id)
            indicators = event.indicators()

            if event.host not in hosts:
                hosts.append(event.host)
            target = indicators.get("target_host")
            if target and target not in hosts:
                hosts.append(target)
            if event.phase() == AttackPhase.EXFILTRATION:
                exfiltrated_mb += indicators["size_mb"]

            event = event.next_event

        return {
            "path": path,
            "compromised_hosts": sorted(hosts),
            "exfiltrated_mb": exfiltrated_mb,
        }
