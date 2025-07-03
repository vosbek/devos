"""
Data models for DevOS daemon
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid

class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"

class CommandType(Enum):
    """Types of commands"""
    FILE_OPERATION = "file_operation"
    GIT_OPERATION = "git_operation"
    PROCESS_MANAGEMENT = "process_management"
    SYSTEM_QUERY = "system_query"
    GENERAL = "general"

@dataclass
class CommandRequest:
    """Command request from user"""
    command: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    approval_timeout: int = 300

@dataclass
class CommandResponse:
    """Response to command request"""
    job_id: str
    status: JobStatus
    requires_approval: bool
    estimated_cost: float
    model_used: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Job:
    """Command execution job"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    command: str = ""
    user_id: str = ""
    status: JobStatus = JobStatus.PENDING
    command_type: CommandType = CommandType.GENERAL
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = field(default_factory=list)
    progress: int = 0
    estimated_completion: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # LLM related fields
    model_used: Optional[str] = None
    tokens_consumed: int = 0
    cost_usd: float = 0.0
    
    # Approval related fields
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    def add_log(self, level: str, message: str, **kwargs):
        """Add log entry to job"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: int, message: str = ""):
        """Update job progress"""
        self.progress = max(0, min(100, progress))
        self.updated_at = datetime.utcnow()
        
        if message:
            self.add_log("INFO", f"Progress {progress}%: {message}")
    
    def set_status(self, status: JobStatus, message: str = ""):
        """Update job status"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if message:
            self.add_log("INFO", f"Status changed to {status.value}: {message}")

@dataclass
class ApprovalRequest:
    """Approval request for command execution"""
    approved: bool
    remember: bool = False
    note: Optional[str] = None

@dataclass
class SystemContext:
    """System context information"""
    cwd: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    files: Dict[str, Any] = field(default_factory=dict)
    processes: Dict[str, Any] = field(default_factory=dict)
    git: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    commands_executed: List[str] = field(default_factory=list)
    files_affected: List[str] = field(default_factory=list)

@dataclass
class ModelUsage:
    """LLM model usage tracking"""
    model_name: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)