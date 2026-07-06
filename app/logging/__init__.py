"""
Structured logging and audit trail.

app.logging.logger configures structlog once at startup for all
application logs. app.logging.audit provides a dedicated audit
channel for authentication, authorization, and tool-execution events,
kept separate so audit trails can be shipped/retained independently.
"""

from app.logging.audit import audit_log, audit_tool_execution
from app.logging.logger import configure_logging, get_logger

__all__ = [
    "configure_logging",
    "get_logger",
    "audit_log",
    "audit_tool_execution",
]