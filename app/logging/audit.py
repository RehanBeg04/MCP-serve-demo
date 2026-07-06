"""
Audit logging.

A dedicated logger for security-relevant events: authentication
attempts, authorization decisions, and tool executions. Kept separate
from general app logs so audit trails can be shipped/retained under
their own policy.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.logging.logger import get_logger

_audit_logger = get_logger("audit")


def audit_log(*, event: str, outcome: str, user_id: str, **extra: Any) -> None:
    from app.auth.context import get_current_correlation_id

    _audit_logger.info(
        event,
        outcome=outcome,
        user_id=user_id,
        correlation_id=get_current_correlation_id(),
        **extra,
    )


@contextmanager
def audit_tool_execution(tool_name: str, user_id: str) -> Iterator[None]:
    """
    Wraps a tool call, emitting a start/end audit entry with duration
    and outcome (success/failure), without swallowing exceptions.
    """
    start = time.monotonic()
    audit_log(event="tool_execution_started", outcome="started", user_id=user_id, tool=tool_name)
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - intentional: we audit, then re-raise
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        audit_log(
            event="tool_execution_failed",
            outcome="failure",
            user_id=user_id,
            tool=tool_name,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
        )
        raise
    else:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        audit_log(
            event="tool_execution_completed",
            outcome="success",
            user_id=user_id,
            tool=tool_name,
            duration_ms=duration_ms,
        )