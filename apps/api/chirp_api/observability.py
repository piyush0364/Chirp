"""Observability, request tracing, and structured logging for Chirp API."""

import contextvars
import json
import logging
import time
import uuid
from typing import Any

# Context variable to hold the current request trace ID
_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


def generate_trace_id() -> str:
    """Generate a unique request trace ID."""
    return f"trace-{uuid.uuid4().hex[:16]}"


def get_trace_id() -> str:
    """Retrieve the trace ID for the active request context.

    If no trace ID is active in context, generates a fallback trace ID.
    """
    trace_id = _trace_id_ctx.get()
    if not trace_id:
        trace_id = generate_trace_id()
        _trace_id_ctx.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> contextvars.Token:
    """Set the trace ID for the active request context."""
    assert isinstance(trace_id, str) and len(trace_id) > 0, "trace_id must be a non-empty string"
    return _trace_id_ctx.set(trace_id)


def reset_trace_id(token: contextvars.Token) -> None:
    """Reset the trace ID context variable."""
    _trace_id_ctx.reset(token)


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON including trace context."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": _trace_id_ctx.get() or getattr(record, "trace_id", ""),
        }

        # Include custom extra fields if provided
        for key, value in record.__dict__.items():
            if key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "trace_id",
            ):
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with structured JSON output."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)


logger = logging.getLogger("chirp_api")
