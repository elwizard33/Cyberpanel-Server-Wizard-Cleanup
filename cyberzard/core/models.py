"""Core data models for cyberzard."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(Enum):
    """Severity levels for findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    """A security finding from a scanner."""
    id: str
    severity: Severity
    description: str
    evidence: Dict[str, Any]
    scanner: str
    timestamp: float


@dataclass
class RemediationAction:
    """A single remediation action."""
    finding_id: Optional[str] = None
    action: Optional[str] = None  # For compatibility
    target: Optional[str] = None
    dry_run: bool = False
    action_type: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    backup_required: bool = True
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.action_type is None and self.action is not None:
            self.action_type = str(self.action)
        if self.description is None:
            self.description = f"Action: {self.action_type or 'unknown'}"


@dataclass
class RemediationPlan:
    """A plan containing multiple remediation actions."""
    actions: List[RemediationAction]
    summary: str
    finding_id: Optional[str] = None
    risk_level: Optional[Severity] = None
    description: Optional[str] = None
    
    
@dataclass
class RemediationResult:
    """Result of a remediation action execution."""
    finding_id: str
    action_type: str
    success: bool
    message: str
    target: Optional[str] = None
    
    def __getitem__(self, key):
        """Allow dict-like access for backwards compatibility."""
        return getattr(self, key)


class ScanResult:
    """Container for scan results."""
    
    def __init__(self):
        self.findings: List[Finding] = []
        
    def add_finding(self, finding: Finding):
        """Add a finding to the results."""
        self.findings.append(finding)
        
    def get_by_severity(self, severity: Severity) -> List[Finding]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]
