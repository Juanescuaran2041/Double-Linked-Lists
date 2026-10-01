# Forensic Attack Timeline Reconstructor

A forensic analyst rebuilds the kill chain of a cyber attack
(reconnaissance → phishing → execution → privilege escalation → lateral
movement → exfiltration) using a **doubly linked list**.

## Why a doubly linked list?

| Need | List operation |
|------|----------------|
| Walk **backwards** from the exfiltration to find patient zero | `node.prev` / `__reversed__` |
| Walk **forwards** from the phishing email to measure the impact | `node.next` / `__iter__` |
| New evidence appears and must land in the middle of the timeline | `insert_sorted` → `insert_before` |
| A false positive must be discarded | `remove(node)` in O(1) |
| The analyst keeps a cursor on the event being analysed | O(1) step in both directions |

## Project structure

```
app/
├── data_structures/      <- YOUR WORK
│   ├── node.py                  Node (data, prev, next)
│   └── doubly_linked_list.py    DoublyLinkedList  (TODO)
├── models/               Domain (OOP)
│   ├── enums.py                 AttackPhase (MITRE ATT&CK), Severity
│   ├── security_event.py        SecurityEvent - abstract base class
│   ├── events.py                6 concrete subclasses (inheritance/polymorphism)
│   └── event_factory.py         Factory Method
├── services/             Business logic
│   ├── attack_timeline.py       AttackTimeline - composes a DoublyLinkedList
│   ├── forensic_investigator.py Cursor navigation + backward/forward tracing
│   └── incident_case.py         Facade used by the API
├── data/sample_incident.py      Fictional incident (inserted out of order)
├── routes/               Flask blueprints (REST API + page)
├── templates/index.html  Frontend
└── static/               CSS + JS
tests/test_doubly_linked_list.py
run.py
```

## Run

```bash
pip install -r requirements.txt
python -m unittest discover tests -v   # validate your list
python run.py                          # http://127.0.0.1:5000
```

While a method is still a TODO, the page shows a banner telling you which
`NotImplementedError` the backend raised.

## OOP principles applied

- **Abstraction**: `SecurityEvent` is an ABC with abstract `phase`, `indicators()` and `summary()`.
- **Encapsulation**: private attributes exposed through read-only properties (`head`, `tail`, `event_id`…).
- **Inheritance**: `PhishingEvent`, `ExfiltrationEvent`, … extend `SecurityEvent`.
- **Polymorphism**: the timeline and frontend treat every event the same way.
- **Composition**: `AttackTimeline` *has a* `DoublyLinkedList`; `IncidentCase` *has a* timeline and an investigator.
- **Patterns**: Factory Method (`EventFactory`), Facade (`IncidentCase`), Application Factory (`create_app`).
