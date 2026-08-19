"""Unit tests for Service Utilities."""

import hashlib
import time

from chirp_api.services.utils import (
    generate_id,
    hash_password,
    to_proto_timestamp,
    verify_password,
)


class TestUtils:
    def test_generate_id(self):
        id1 = generate_id()
        id2 = generate_id()
        assert isinstance(id1, str)
        assert len(id1) > 0
        assert id1 != id2

    def test_hash_and_verify_password(self):
        plain = "secure_password_123!"
        hashed = hash_password(plain)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        is_valid, is_legacy = verify_password(plain, hashed)
        assert is_valid is True
        assert is_legacy is False

        is_valid_wrong, _ = verify_password("wrong_password", hashed)
        assert is_valid_wrong is False

    def test_verify_legacy_sha256_hash(self):
        plain = "old_legacy_pw"
        legacy_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        is_valid, is_legacy = verify_password(plain, legacy_hash)
        assert is_valid is True
        assert is_legacy is True

        is_valid_wrong, _ = verify_password("incorrect_pw", legacy_hash)
        assert is_valid_wrong is False

    def test_to_proto_timestamp(self):
        now_epoch = int(time.time())
        proto_ts = to_proto_timestamp(now_epoch)
        assert proto_ts.seconds == now_epoch
        assert proto_ts.nanos == 0

        # None epoch fallback
        proto_ts_none = to_proto_timestamp(None)
        assert proto_ts_none.seconds == 0
