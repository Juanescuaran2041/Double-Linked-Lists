# Forensic Attack Timeline Reconstructor

A forensic analyst rebuilds the kill chain of a cyber attack
(reconnaissance → phishing → execution → privilege escalation → lateral
movement → exfiltration) using a **doubly linked list**.

## Why a doubly linked list?

Every `SecurityEvent` is a link of the chain (`previous_event` / `next_event`)
and `AttackTimeline` is the list (`first_event`, `last_event`, `size`).

| Need | Timeline operation |
|------|--------------------|
| Walk **backwards** from the exfiltration to find patient zero | `previous_event` / `__reversed__` |
| Walk **forwards** from the phishing email to measure the impact | `next_event` / `__iter__` |
| New evidence must land in the middle of the timeline | `add_event` → `insert_event_before` |
| A false positive must be discarded | `remove_event` in O(1) |
| The analyst keeps a cursor on the event being analysed | O(1) step in both directions |

## Project structure

```
app/
├── models/
│   ├── attack_timeline.py       AttackTimeline - the doubly linked list
│   ├── security_event.py        SecurityEvent - abstract base, each event is a link
│   ├── events.py                6 concrete events (inheritance/polymorphism)
│   ├── enums.py                 AttackPhase (MITRE ATT&CK), Severity
│   └── event_factory.py         Factory: builds events from the UI form
├── services/
│   ├── forensic_investigator.py Cursor navigation + backward/forward tracing
│   └── incident_case.py         Facade used by the API
├── routes/               Flask blueprints (REST API + page)
├── templates/index.html  Frontend
└── static/               CSS + JS
tests/test_attack_timeline.py
run.py
```

The case starts **empty**: all evidence is added by the analyst from the UI.

## Run

```bash
pip install -r requirements.txt
python -m unittest discover tests -v   # run the unit tests
python run.py                          # http://127.0.0.1:5000
```

## OOP principles applied

- **Abstraction**: `SecurityEvent` is an ABC with abstract `phase`, `indicators()` and `summary()`.
- **Inheritance**: `PhishingEvent`, `ExfiltrationEvent`, … extend `SecurityEvent`.
- **Polymorphism**: the timeline and frontend treat every event the same way.
- **Composition**: `IncidentCase` *has a* timeline and an investigator; the investigator *has a* timeline.
- **Patterns**: Factory Method (`EventFactory`), Facade (`IncidentCase`), Application Factory (`create_app`).
