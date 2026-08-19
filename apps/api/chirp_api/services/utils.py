"""Utility functions for Chirp API services.

Contains ID generation, password hashing, and timestamp conversion.
"""

import hashlib
import random
import string
import time

import bcrypt


def generate_id() -> str:
    """Generate a simple unique ID: timestamp-random."""
    timestamp = int(time.time() * 1000)
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    result = f"{timestamp}-{random_str}"
    assert len(result) > 0, "Generated ID must not be empty"
    return result


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    assert isinstance(password, str), "Password must be a string"
    assert len(password) > 0, "Password must not be empty"
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> tuple[bool, bool]:
    """Verify password against stored hash. Returns (is_valid, needs_upgrade)."""
    assert isinstance(password, str), "Password must be a string"
    assert isinstance(hashed, str), "Hash must be a string"

    legacy_hashes = [
        hashlib.sha256((password + "salt").encode()).hexdigest(),
        hashlib.sha256(password.encode("utf-8")).hexdigest(),
    ]

    try:
        # First try checking against the plaintext password
        if bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
            return True, False

        # If that fails, compute the legacy SHA-256 hash and check against the stored bcrypt hash.
        for leg_h in legacy_hashes:
            if bcrypt.checkpw(leg_h.encode("utf-8"), hashed.encode("utf-8")):
                return True, True
    except ValueError:
        pass

    # Final fallback for unmigrated legacy hashes (needed for zero-downtime migration)
    for leg_h in legacy_hashes:
        if leg_h == hashed:
            return True, True

    return False, False


def to_proto_timestamp(dt):
    """Convert datetime or unix timestamp int to proto Timestamp message."""
    from chirp_api.generated import common_pb2

    if dt is None:
        return common_pb2.Timestamp(seconds=0, nanos=0)
    if isinstance(dt, int):
        return common_pb2.Timestamp(seconds=dt, nanos=0)
    return common_pb2.Timestamp(seconds=int(dt.timestamp()), nanos=0)
