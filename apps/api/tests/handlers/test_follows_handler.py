"""Tests for FollowsService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import follows_pb2
from chirp_api.handlers.follows_handler import FollowsServiceServicer


@pytest.fixture
def servicer():
    return FollowsServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestFollowsHandler:
    @patch("chirp_api.handlers.follows_handler.toggle_follow")
    @patch("chirp_api.handlers.follows_handler.validate_session_token")
    @patch("chirp_api.handlers.follows_handler.SessionLocal")
    def test_toggle_follow(
        self, mock_session_cls, mock_validate, mock_toggle, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_toggle.return_value = {"following": True}

        request = follows_pb2.ToggleFollowRequest(
            username="targetuser",
            session_token="valid-token",
        )

        response = servicer.ToggleFollow(request, context)
        assert response.success is True
        assert response.following is True

    @patch("chirp_api.handlers.follows_handler.get_follow_status")
    @patch("chirp_api.handlers.follows_handler.validate_session_token")
    @patch("chirp_api.handlers.follows_handler.SessionLocal")
    def test_get_follow_status(
        self, mock_session_cls, mock_validate, mock_status, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_status.return_value = {"following": True}

        request = follows_pb2.GetFollowStatusRequest(
            username="targetuser",
            session_token="valid-token",
        )

        response = servicer.GetFollowStatus(request, context)
        assert response.following is True

    @patch("chirp_api.handlers.follows_handler.get_follower_count")
    @patch("chirp_api.handlers.follows_handler.SessionLocal")
    def test_get_follower_count(
        self, mock_session_cls, mock_count, servicer, context
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_count.return_value = {"count": 42}

        request = follows_pb2.GetCountRequest(username="targetuser")
        response = servicer.GetFollowerCount(request, context)
        assert response.count == 42
