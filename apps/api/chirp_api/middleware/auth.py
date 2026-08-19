"""JWT authentication middleware for Chirp API.

Uses PyJWT with HS256 signing.
"""

import os
import time

import jwt

from chirp_api.errors import AuthenticationError, PermissionDeniedError

JWT_SECRET = os.environ.get("GRPC_JWT_SECRET", "chirp-grpc-jwt-secret-key-at-least-32-chars")

TOKEN_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 days


def validate_session_token(token: str) -> dict:
    """Validate a session token and return the auth context.

    Returns dict with userId, username, role.
    Raises AuthenticationError if token is invalid or expired.
    """
    assert isinstance(token, str), "Token must be a string"
    assert len(token) > 0, "Token must not be empty"

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        result = {
            "user_id": decoded["userId"],
            "username": decoded["username"],
            "role": decoded["role"],
        }
        assert result["user_id"], "Token must contain userId"
        assert result["username"], "Token must contain username"
        assert result["role"], "Token must contain role"
        return result
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Invalid or expired session token")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid or expired session token")
    except KeyError:
        raise AuthenticationError("Invalid or expired session token")


def create_session_token(
    user_id: str, username: str, role: str, expires_in_seconds: int = TOKEN_EXPIRY_SECONDS
) -> str:
    """Create a session token from user info.

    Returns JWT string.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be a non-empty string"
    assert isinstance(username, str) and len(username) > 0, "username must be a non-empty string"
    assert role in ("user", "admin", "moderator"), f"Invalid role: {role}"

    payload = {
        "userId": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + expires_in_seconds,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    assert isinstance(token, str), "Encoded token must be a string"
    return token


def require_auth(token: str | None) -> dict:
    """Require authentication. Raises AuthenticationError if token is missing or invalid.

    Returns auth context dict with userId, username, role.
    """
    if not token:
        raise AuthenticationError("Authentication required")
    return validate_session_token(token)


def require_admin(context: dict) -> None:
    """Require admin or moderator role. Raises PermissionDeniedError if not authorized."""
    assert isinstance(context, dict), "Context must be a dict"
    if context.get("role") not in ("admin", "moderator"):
        raise PermissionDeniedError("Admin access required")


def require_super_admin(context: dict) -> None:
    """Require admin role specifically. Raises PermissionDeniedError if not authorized."""
    assert isinstance(context, dict), "Context must be a dict"
    if context.get("role") != "admin":
        raise PermissionDeniedError("Super admin access required")
