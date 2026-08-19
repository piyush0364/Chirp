"""Unit tests for Notifications Service."""

import pytest

from chirp_api.services.notifications_service import (
    create_notification,
    delete_notification,
    get_unread_count,
    get_user_notifications,
    mark_all_as_read,
    mark_as_read,
)
from tests.helpers import (
    create_test_notification,
    create_test_post,
    create_test_user,
)


class TestNotificationsService:
    def test_create_and_get_notifications(self, session):
        user = create_test_user(session)
        actor = create_test_user(session)
        post = create_test_post(session, user.id, "Hello")

        notif = create_notification(
            session,
            user_id=user.id,
            notification_type="like",
            actor_id=actor.id,
            post_id=post.id,
        )

        assert notif is not None
        notifications = get_user_notifications(session, user.id)
        assert len(notifications) == 1
        assert notifications[0]["id"] == notif["notification_id"]
        assert notifications[0]["actor"]["id"] == actor.id
        assert notifications[0]["post_content"] == "Hello"

    def test_create_self_notification_returns_none(self, session):
        user = create_test_user(session)
        post = create_test_post(session, user.id, "Self post")

        notif = create_notification(
            session,
            user_id=user.id,
            notification_type="like",
            actor_id=user.id,
            post_id=post.id,
        )
        assert notif is None

    def test_get_unread_count_and_mark_read(self, session):
        user = create_test_user(session)
        actor = create_test_user(session)

        n1 = create_test_notification(session, user.id, actor.id, type="follow", read=False)
        create_test_notification(session, user.id, actor.id, type="like", read=False)

        count = get_unread_count(session, user.id)
        assert count["count"] == 2

        mark_as_read(session, n1.id, user.id)
        count_after = get_unread_count(session, user.id)
        assert count_after["count"] == 1

        mark_all_as_read(session, user.id)
        count_final = get_unread_count(session, user.id)
        assert count_final["count"] == 0

    def test_delete_notification(self, session):
        user = create_test_user(session)
        actor = create_test_user(session)
        n1 = create_test_notification(session, user.id, actor.id, type="follow")

        delete_notification(session, n1.id, user.id)
        notifications = get_user_notifications(session, user.id)
        assert len(notifications) == 0

    def test_delete_notification_not_owner(self, session):
        user = create_test_user(session)
        other_user = create_test_user(session)
        actor = create_test_user(session)
        n1 = create_test_notification(session, user.id, actor.id, type="follow")

        with pytest.raises(Exception, match="Unauthorized"):
            delete_notification(session, n1.id, other_user.id)
