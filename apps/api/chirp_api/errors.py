"""Unified error taxonomy for Chirp API.

Defines standardized domain exceptions and their mappings to gRPC Status Codes.
"""

from typing import Any

import grpc


class ChirpError(Exception):
    """Base exception for all Chirp domain errors."""

    status_code: grpc.StatusCode = grpc.StatusCode.INTERNAL

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ChirpError):
    """Raised when client input fails validation rules (maps to INVALID_ARGUMENT)."""

    status_code = grpc.StatusCode.INVALID_ARGUMENT


class AuthenticationError(ChirpError):
    """Raised when credentials/tokens are invalid or expired (maps to UNAUTHENTICATED)."""

    status_code = grpc.StatusCode.UNAUTHENTICATED


class PermissionDeniedError(ChirpError):
    """Raised when user lacks permissions for an action (maps to PERMISSION_DENIED)."""

    status_code = grpc.StatusCode.PERMISSION_DENIED


class NotFoundError(ChirpError):
    """Raised when a requested resource does not exist (maps to NOT_FOUND)."""

    status_code = grpc.StatusCode.NOT_FOUND


class AlreadyExistsError(ChirpError):
    """Raised when attempting to create a resource that already exists (maps to ALREADY_EXISTS)."""

    status_code = grpc.StatusCode.ALREADY_EXISTS


class FailedPreconditionError(ChirpError):
    """Raised when operation cannot be performed in current state (maps to FAILED_PRECONDITION)."""

    status_code = grpc.StatusCode.FAILED_PRECONDITION


class ResourceExhaustedError(ChirpError):
    """Raised when rate limits or quotas are exceeded (maps to RESOURCE_EXHAUSTED)."""

    status_code = grpc.StatusCode.RESOURCE_EXHAUSTED


class InternalError(ChirpError):
    """Raised for unexpected server errors (maps to INTERNAL)."""

    status_code = grpc.StatusCode.INTERNAL


def map_error_to_status_code(error: Exception) -> tuple[grpc.StatusCode, str]:
    """Map any Python exception to an appropriate gRPC status code and safe message."""
    if isinstance(error, ChirpError):
        return error.status_code, error.message

    # Fallback heuristic mapping for common service exceptions
    error_msg = str(error)
    lower_msg = error_msg.lower()

    auth_keywords = ("unauthenticated", "auth", "token", "session", "credentials", "login")
    if any(k in lower_msg for k in auth_keywords):
        return grpc.StatusCode.UNAUTHENTICATED, error_msg

    perm_keywords = (
        "unauthorized",
        "admin access",
        "permission",
        "only edit your own",
        "forbidden",
    )
    if any(k in lower_msg for k in perm_keywords):
        return grpc.StatusCode.PERMISSION_DENIED, error_msg
    if "not found" in lower_msg:
        return grpc.StatusCode.NOT_FOUND, error_msg
    if any(k in lower_msg for k in ("already exists", "duplicate", "taken")):
        return grpc.StatusCode.ALREADY_EXISTS, error_msg
    if any(k in lower_msg for k in ("required", "invalid", "must be", "exceeds", "negative")):
        return grpc.StatusCode.INVALID_ARGUMENT, error_msg

    return grpc.StatusCode.INTERNAL, error_msg
