"""Unit tests for Bookmarks Service."""

import pytest

from chirp_api.services.bookmarks_service import (
    get_bookmark_status,
    get_bookmarked_posts,
    toggle_bookmark,
)
from tests.helpers import create_test_bookmark, create_test_post, create_test_user


class TestToggleBookmark:
    def test_toggle_bookmark_on(self, session):
        user = create_test_user(session)
        post = create_test_post(session, user.id)

        result = toggle_bookmark(session, post.id, user.id)
        assert result["bookmarked"] is True

        status = get_bookmark_status(session, post.id, user.id)
        assert status["bookmarked"] is True

    def test_toggle_bookmark_off(self, session):
        user = create_test_user(session)
        post = create_test_post(session, user.id)
        create_test_bookmark(session, user.id, post.id)

        result = toggle_bookmark(session, post.id, user.id)
        assert result["bookmarked"] is False

        status = get_bookmark_status(session, post.id, user.id)
        assert status["bookmarked"] is False

    def test_toggle_bookmark_post_not_found(self, session):
        user = create_test_user(session)
        with pytest.raises(Exception, match="Post not found"):
            toggle_bookmark(session, "nonexistent-post-id", user.id)


class TestGetBookmarkedPosts:
    def test_get_bookmarked_posts(self, session):
        user = create_test_user(session)
        other_user = create_test_user(session)
        post1 = create_test_post(session, other_user.id, "Post 1")
        post2 = create_test_post(session, other_user.id, "Post 2")
        create_test_bookmark(session, user.id, post1.id)
        create_test_bookmark(session, user.id, post2.id)

        posts = get_bookmarked_posts(session, user.id, user.id, limit=10, offset=0)
        assert len(posts) == 2
        assert posts[0]["id"] in (post1.id, post2.id)
        assert posts[0]["is_liked"] is False

    def test_get_bookmarked_posts_empty(self, session):
        user = create_test_user(session)
        posts = get_bookmarked_posts(session, user.id, user.id)
        assert posts == []
