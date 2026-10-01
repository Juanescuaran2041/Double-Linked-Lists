from datetime import datetime

from app.models.enums import AttackPhase, Severity
from app.models.security_event import SecurityEvent


class ReconnaissanceEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, source_ip: str, ports_scanned: int) -> None:
        super().__init__(timestamp, host, description, severity)
        self._source_ip = source_ip
        self._ports_scanned = int(ports_scanned)

    def phase(self) -> AttackPhase:
        return AttackPhase.RECONNAISSANCE

    def indicators(self) -> dict:
        return {"source_ip": self._source_ip, "ports_scanned": self._ports_scanned}

    def summary(self) -> str:
        return f"Port scan from {self._source_ip} ({self._ports_scanned} ports)"


class PhishingEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, sender: str, subject: str) -> None:
        super().__init__(timestamp, host, description, severity)
        self._sender = sender
        self._subject = subject

    def phase(self) -> AttackPhase:
        return AttackPhase.INITIAL_ACCESS

    def indicators(self) -> dict:
        return {"sender": self._sender, "subject": self._subject}

    def summary(self) -> str:
        return f"Phishing email from {self._sender}"


class MalwareExecutionEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, process: str, sha256: str) -> None:
        super().__init__(timestamp, host, description, severity)
        self._process = process
        self._sha256 = sha256

    def phase(self) -> AttackPhase:
        return AttackPhase.EXECUTION

    def indicators(self) -> dict:
        return {"process": self._process, "sha256": self._sha256}

    def summary(self) -> str:
        return f"Malicious process {self._process} executed"


class PrivilegeEscalationEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, account: str, technique: str) -> None:
        super().__init__(timestamp, host, description, severity)
        self._account = account
        self._technique = technique

    def phase(self) -> AttackPhase:
        return AttackPhase.PRIVILEGE_ESCALATION

    def indicators(self) -> dict:
        return {"account": self._account, "technique": self._technique}

    def summary(self) -> str:
        return f"{self._account} escalated via {self._technique}"


class LateralMovementEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, target_host: str, protocol: str) -> None:
        super().__init__(timestamp, host, description, severity)
        self._target_host = target_host
        self._protocol = protocol

    def phase(self) -> AttackPhase:
        return AttackPhase.LATERAL_MOVEMENT

    def indicators(self) -> dict:
        return {"target_host": self._target_host, "protocol": self._protocol}

    def summary(self) -> str:
        return f"{self.host} -> {self._target_host} over {self._protocol}"


class ExfiltrationEvent(SecurityEvent):
    def __init__(self, timestamp: datetime, host: str, description: str,
                 severity: Severity, destination: str, size_mb: float) -> None:
        super().__init__(timestamp, host, description, severity)
        self._destination = destination
        self._size_mb = float(size_mb)

    def phase(self) -> AttackPhase:
        return AttackPhase.EXFILTRATION

    def indicators(self) -> dict:
        return {"destination": self._destination, "size_mb": self._size_mb}

    def summary(self) -> str:
        return f"{self._size_mb} MB sent to {self._destination}"
