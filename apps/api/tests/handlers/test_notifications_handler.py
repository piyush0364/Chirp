"""Tests for NotificationsService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import notifications_pb2
from chirp_api.handlers.notifications_handler import NotificationsServiceServicer


@pytest.fixture
def servicer():
    return NotificationsServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestNotificationsHandler:
    @patch("chirp_api.handlers.notifications_handler.get_user_notifications")
    @patch("chirp_api.handlers.notifications_handler.validate_session_token")
    @patch("chirp_api.handlers.notifications_handler.SessionLocal")
    def test_get_notifications(
        self, mock_session_cls, mock_validate, mock_notifs, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_notifs.return_value = [
            {
                "id": "notif-1",
                "type": "like",
                "read": False,
                "created_at": 1700000000,
                "actor": {
                    "id": "actor-1",
                    "username": "actor",
                    "display_name": "Actor",
                    "avatar_url": "",
                },
                "post_id": "post-1",
                "post_content": "Post snippet",
            }
        ]

        request = notifications_pb2.GetNotificationsRequest(
            session_token="valid-token",
        )

        response = servicer.GetNotifications(request, context)
        assert len(response.notifications) == 1
        assert response.notifications[0].id == "notif-1"

    @patch("chirp_api.handlers.notifications_handler.get_unread_count")
    @patch("chirp_api.handlers.notifications_handler.validate_session_token")
    @patch("chirp_api.handlers.notifications_handler.SessionLocal")
    def test_get_unread_count(
        self, mock_session_cls, mock_validate, mock_count, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_count.return_value = {"count": 3}

        request = notifications_pb2.GetUnreadCountRequest(session_token="valid-token")
        response = servicer.GetUnreadCount(request, context)
        assert response.count == 3

    @patch("chirp_api.handlers.notifications_handler.mark_as_read")
    @patch("chirp_api.handlers.notifications_handler.validate_session_token")
    @patch("chirp_api.handlers.notifications_handler.SessionLocal")
    def test_mark_as_read(
        self, mock_session_cls, mock_validate, mock_mark, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth

        request = notifications_pb2.MarkAsReadRequest(
            notification_id="notif-1",
            session_token="valid-token",
        )
        response = servicer.MarkAsRead(request, context)
        assert response.success is True

    @patch("chirp_api.handlers.notifications_handler.delete_notification")
    @patch("chirp_api.handlers.notifications_handler.validate_session_token")
    @patch("chirp_api.handlers.notifications_handler.SessionLocal")
    def test_delete_notification(
        self, mock_session_cls, mock_validate, mock_del, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth

        request = notifications_pb2.DeleteNotificationRequest(
            notification_id="notif-1",
            session_token="valid-token",
        )
        response = servicer.DeleteNotification(request, context)
        assert response.success is True
