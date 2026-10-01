from app.models.security_event import SecurityEvent


class AttackTimeline:

    def __init__(self) -> None:
        self.first_event: SecurityEvent | None = None
        self.last_event: SecurityEvent | None = None
        self.size = 0

    def __len__(self) -> int:
        return self.size

    def is_empty(self) -> bool:
        return self.size == 0

    def append_event(self, event: SecurityEvent) -> None:
        if self.is_empty():
            self.first_event = event
        else:
            event.previous_event = self.last_event
            self.last_event.next_event = event
        self.last_event = event
        self.size += 1

    def prepend_event(self, event: SecurityEvent) -> None:
        if self.is_empty():
            self.last_event = event
        else:
            event.next_event = self.first_event
            self.first_event.previous_event = event
        self.first_event = event
        self.size += 1

    def insert_event_before(self, reference: SecurityEvent, event: SecurityEvent) -> None:
        if reference is self.first_event:
            self.prepend_event(event)
            return

        event.previous_event = reference.previous_event
        event.next_event = reference
        reference.previous_event.next_event = event
        reference.previous_event = event
        self.size += 1

    def add_event(self, event: SecurityEvent) -> None:
        if self.is_empty() or event.timestamp >= self.last_event.timestamp:
            self.append_event(event)
            return

        current_event = self.first_event
        while current_event.timestamp <= event.timestamp:
            current_event = current_event.next_event

        self.insert_event_before(current_event, event)

    def remove_event(self, event: SecurityEvent) -> SecurityEvent:
        if event.previous_event is None:
            self.first_event = event.next_event
        else:
            event.previous_event.next_event = event.next_event

        if event.next_event is None:
            self.last_event = event.previous_event
        else:
            event.next_event.previous_event = event.previous_event

        event.previous_event = None
        event.next_event = None
        self.size -= 1
        return event

    def clear(self) -> None:
        self.first_event = None
        self.last_event = None
        self.size = 0

    def find_event(self, event_id: str) -> SecurityEvent | None:
        for event in self:
            if event.event_id == event_id:
                return event
        return None

    def __iter__(self):
        current_event = self.first_event
        while current_event is not None:
            yield current_event
            current_event = current_event.next_event

    def __reversed__(self):
        current_event = self.last_event
        while current_event is not None:
            yield current_event
            current_event = current_event.previous_event

    def phase_stats(self) -> dict:
        stats = {}
        for event in self:
            name = event.phase().name
            stats[name] = stats.get(name, 0) + 1
        return stats
