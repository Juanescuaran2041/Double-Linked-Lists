from enum import Enum

class AttackPhase(Enum):

    RECONNAISSANCE = (1, "TA0043", "Reconnaissance", "#38bdf8")
    INITIAL_ACCESS = (2, "TA0001", "Initial Access", "#a78bfa")
    EXECUTION = (3, "TA0002", "Execution", "#f472b6")
    PRIVILEGE_ESCALATION = (4, "TA0004", "Privilege Escalation", "#fb923c")
    LATERAL_MOVEMENT = (5, "TA0008", "Lateral Movement", "#facc15")
    EXFILTRATION = (6, "TA0010", "Exfiltration", "#f43f5e")

    def __init__(self, order: int, tactic_id: str, label: str, color: str) -> None:
        self.order = order
        self.tactic_id = tactic_id
        self.label = label
        self.color = color

class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def from_name(cls, name: str) -> "Severity":
        return cls[name.upper()]
        
