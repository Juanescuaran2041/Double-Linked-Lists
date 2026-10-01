"""Unit tests for YOUR AttackTimeline (doubly linked list) implementation.

Run:  python -m unittest discover tests -v
"""

import unittest
from datetime import datetime

from app.models import AttackTimeline, Severity
from app.models.events import PhishingEvent


def make_event(hour: int, minute: int = 0) -> PhishingEvent:
    return PhishingEvent(datetime(2026, 9, 14, hour, minute), "WS-01", "",
                         Severity.HIGH, "attacker@evil.test", f"mail {hour}:{minute}")


class AttackTimelineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline = AttackTimeline()

    def assertChain(self, expected: list) -> None:
        """Checks the order in both directions AND every link."""
        self.assertEqual(len(self.timeline), len(expected))
        self.assertEqual(list(self.timeline), expected)
        self.assertEqual(list(reversed(self.timeline)), expected[::-1])
        if not expected:
            self.assertIsNone(self.timeline.first_event)
            self.assertIsNone(self.timeline.last_event)
            return
        self.assertIsNone(self.timeline.first_event.previous_event)
        self.assertIsNone(self.timeline.last_event.next_event)
        event = self.timeline.first_event
        while event.next_event:
            self.assertIs(event.next_event.previous_event, event)
            event = event.next_event
        self.assertIs(event, self.timeline.last_event)


class TestInsertion(AttackTimelineTestCase):
    def test_new_timeline_is_empty(self):
        self.assertTrue(self.timeline.is_empty())
        self.assertChain([])

    def test_append_event(self):
        events = [make_event(h) for h in (1, 2, 3)]
        for e in events:
            self.timeline.append_event(e)
        self.assertChain(events)

    def test_prepend_event(self):
        a, b, c = make_event(1), make_event(2), make_event(3)
        for e in (c, b, a):
            self.timeline.prepend_event(e)
        self.assertChain([a, b, c])

    def test_insert_event_before_middle_and_first(self):
        a, b, c = make_event(1), make_event(2), make_event(3)
        self.timeline.append_event(c)
        self.timeline.insert_event_before(c, b)
        self.timeline.insert_event_before(b, a)
        self.assertChain([a, b, c])

    def test_add_event_sorts_by_timestamp(self):
        events = {h: make_event(h) for h in (5, 1, 4, 2, 3, 0, 6)}
        for e in events.values():
            self.timeline.add_event(e)
        self.assertChain([events[h] for h in range(7)])

    def test_add_event_same_timestamp_goes_after(self):
        first, second = make_event(10), make_event(10)
        self.timeline.add_event(first)
        self.timeline.add_event(second)
        self.assertChain([first, second])


class TestRemoval(AttackTimelineTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.events = [make_event(h) for h in (1, 2, 3, 4)]
        for e in self.events:
            self.timeline.append_event(e)

    def test_remove_middle(self):
        removed = self.timeline.remove_event(self.events[1])
        self.assertIs(removed, self.events[1])
        self.assertChain([self.events[0], self.events[2], self.events[3]])

    def test_remove_first(self):
        self.timeline.remove_event(self.events[0])
        self.assertChain(self.events[1:])

    def test_remove_last(self):
        self.timeline.remove_event(self.events[3])
        self.assertChain(self.events[:3])

    def test_remove_all(self):
        for e in self.events:
            self.timeline.remove_event(e)
        self.assertChain([])

    def test_removed_event_is_unlinked(self):
        event = self.events[2]
        self.timeline.remove_event(event)
        self.assertIsNone(event.previous_event)
        self.assertIsNone(event.next_event)

    def test_clear(self):
        self.timeline.clear()
        self.assertChain([])
        new = make_event(9)
        self.timeline.append_event(new)
        self.assertChain([new])


class TestSearch(AttackTimelineTestCase):
    def test_find_event(self):
        events = [make_event(h) for h in (1, 2, 3)]
        for e in events:
            self.timeline.append_event(e)
        self.assertIs(self.timeline.find_event(events[1].event_id), events[1])
        self.assertIsNone(self.timeline.find_event("EVT-9999"))

    def test_find_event_on_empty_timeline(self):
        self.assertIsNone(self.timeline.find_event("EVT-0001"))


if __name__ == "__main__":
    unittest.main()
