"""Unit tests for Users Service."""

import pytest

from chirp_api.services.users_service import get_user, update_profile
from tests.helpers import (
    create_test_follow,
    create_test_post,
    create_test_user,
)


class TestUsersService:
    def test_get_user_with_counts(self, session):
        user = create_test_user(session)
        follower = create_test_user(session)
        followed = create_test_user(session)

        create_test_follow(session, follower.id, user.id)
        create_test_follow(session, user.id, followed.id)
        create_test_post(session, user.id, "Post 1")
        create_test_post(session, user.id, "Post 2")

        profile = get_user(session, user.username, requester_id=follower.id)
        assert profile["id"] == user.id
        assert profile["follower_count"] == 1
        assert profile["following_count"] == 1
        assert profile["post_count"] == 2
        assert profile["is_following"] is True

    def test_get_user_not_found(self, session):
        with pytest.raises(Exception, match="User not found"):
            get_user(session, "nonexistent-username")

    def test_update_profile(self, session):
        user = create_test_user(session)
        res = update_profile(
            session,
            user_id=user.id,
            display_name="Updated Name",
            bio="New bio content",
            avatar_url="https://example.com/avatar.png",
        )
        assert res["success"] is True

        profile = get_user(session, user.username)
        assert profile["display_name"] == "Updated Name"
        assert profile["bio"] == "New bio content"
        assert profile["avatar_url"] == "https://example.com/avatar.png"

    def test_update_profile_not_found(self, session):
        with pytest.raises(Exception, match="User not found"):
            update_profile(session, "nonexistent-id", display_name="Test")
