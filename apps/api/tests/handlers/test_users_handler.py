"""Tests for UsersService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import users_pb2
from chirp_api.handlers.users_handler import UsersServiceServicer


@pytest.fixture
def servicer():
    return UsersServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestUsersHandler:
    @patch("chirp_api.handlers.users_handler.get_user")
    @patch("chirp_api.handlers.users_handler.SessionLocal")
    def test_get_user(self, mock_session_cls, mock_get_user, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_user.return_value = {
            "id": "u-1",
            "email": "user@test.com",
            "username": "targetuser",
            "display_name": "Target User",
            "avatar_url": "",
            "bio": "Developer",
            "role": "user",
            "created_at": 1700000000,
            "follower_count": 5,
            "following_count": 2,
            "post_count": 10,
            "is_following": False,
        }

        request = users_pb2.GetUserRequest(username="targetuser")
        response = servicer.GetUser(request, context)
        assert response.id == "u-1"
        assert response.username == "targetuser"
        assert response.follower_count == 5

    @patch("chirp_api.handlers.users_handler.update_profile")
    @patch("chirp_api.handlers.users_handler.validate_session_token")
    @patch("chirp_api.handlers.users_handler.SessionLocal")
    def test_update_profile(
        self, mock_session_cls, mock_validate, mock_update, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_update.return_value = {"success": True}

        request = users_pb2.UpdateProfileRequest(
            session_token="valid-token",
            display_name="New Name",
            bio="New Bio",
        )

        response = servicer.UpdateProfile(request, context)
        assert response.success is True
