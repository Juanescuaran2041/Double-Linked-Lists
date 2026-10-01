from enum import Enum


class AttackPhase(Enum):
    RECONNAISSANCE = ("TA0043", "Reconnaissance", "#38bdf8")
    INITIAL_ACCESS = ("TA0001", "Initial Access", "#a78bfa")
    EXECUTION = ("TA0002", "Execution", "#f472b6")
    PRIVILEGE_ESCALATION = ("TA0004", "Privilege Escalation", "#fb923c")
    LATERAL_MOVEMENT = ("TA0008", "Lateral Movement", "#facc15")
    EXFILTRATION = ("TA0010", "Exfiltration", "#f43f5e")

    def __init__(self, tactic_id: str, label: str, color: str) -> None:
        self.tactic_id = tactic_id
        self.label = label
        self.color = color


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
