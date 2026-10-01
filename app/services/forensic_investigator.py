"""Forensic investigator: navigates the timeline with an event cursor."""

from typing import Any, Dict, List, Optional

from app.models import AttackPhase, AttackTimeline, SecurityEvent


class ForensicInvestigator:
    """Keeps a pointer to the event under analysis.

    Moving one step in either direction is O(1) thanks to
    ``previous_event`` / ``next_event``: the reason for a DOUBLY linked list.
    """

    def __init__(self, timeline: AttackTimeline) -> None:
        self._timeline = timeline
        self.current: Optional[SecurityEvent] = None

    # ---- navigation -------------------------------------------------- #
    def go_to_first(self) -> None:
        self.current = self._timeline.first_event

    def go_to_last(self) -> None:
        self.current = self._timeline.last_event

    def step_forward(self) -> None:
        if self.current and self.current.next_event:
            self.current = self.current.next_event

    def step_backward(self) -> None:
        if self.current and self.current.previous_event:
            self.current = self.current.previous_event

    def jump_to(self, event_id: str) -> None:
        event = self._timeline.find_event(event_id)
        if event is None:
            raise KeyError(f"Event {event_id} not found")
        self.current = event

    def release(self, event: SecurityEvent) -> None:
        """Move the cursor away from an event that is about to be removed."""
        if self.current is event:
            self.current = event.next_event or event.previous_event

    # ---- analysis ---------------------------------------------------- #
    def trace_to_patient_zero(self) -> Dict[str, Any]:
        """Walk BACKWARDS from the cursor to find how the attacker got in."""
        path: List[SecurityEvent] = []
        event = self.current
        while event:
            path.append(event)
            event = event.previous_event

        entry_points = [e for e in path if e.phase() is AttackPhase.INITIAL_ACCESS]
        patient_zero = entry_points[-1] if entry_points else (path[-1] if path else None)
        return {
            "path": [e.event_id for e in path],
            "patient_zero": patient_zero.to_dict() if patient_zero else None,
        }

    def trace_impact(self) -> Dict[str, Any]:
        """Walk FORWARDS from the cursor to measure the blast radius."""
        path: List[SecurityEvent] = []
        event = self.current
        while event:
            path.append(event)
            event = event.next_event

        hosts = set()
        for e in path:
            hosts.add(e.host)
            target = e.indicators().get("target_host")
            if target:
                hosts.add(target)
        return {
            "path": [e.event_id for e in path],
            "compromised_hosts": sorted(hosts),
            "exfiltrated_mb": sum(
                e.indicators().get("size_mb", 0) for e in path
                if e.phase() is AttackPhase.EXFILTRATION
            ),
        }
