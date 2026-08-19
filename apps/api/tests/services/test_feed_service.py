"""Unit tests for Feed Service."""

from chirp_api.services.feed_service import get_explore_feed, get_home_feed
from tests.helpers import create_test_follow, create_test_like, create_test_post, create_test_user


class TestHomeFeed:
    def test_get_home_feed_includes_followed_and_own_posts(self, session):
        user = create_test_user(session)
        followed_user = create_test_user(session)
        unfollowed_user = create_test_user(session)

        create_test_follow(session, user.id, followed_user.id)

        own_post = create_test_post(session, user.id, "My post")
        followed_post = create_test_post(session, followed_user.id, "Followed post")
        unfollowed_post = create_test_post(session, unfollowed_user.id, "Unfollowed post")

        feed = get_home_feed(session, user.id, limit=20, offset=0)
        feed_ids = [p["id"] for p in feed]

        assert own_post.id in feed_ids
        assert followed_post.id in feed_ids
        assert unfollowed_post.id not in feed_ids

    def test_get_home_feed_empty(self, session):
        user = create_test_user(session)
        feed = get_home_feed(session, user.id)
        assert feed == []


class TestExploreFeed:
    def test_get_explore_feed_public(self, session):
        author = create_test_user(session)
        post = create_test_post(session, author.id, "Public post")

        feed = get_explore_feed(session, limit=10, offset=0, user_id=None)
        assert len(feed) >= 1
        found = next((p for p in feed if p["id"] == post.id), None)
        assert found is not None
        assert found["author"]["username"] == author.username
        assert found["is_liked"] is False

    def test_get_explore_feed_with_like_status(self, session):
        user = create_test_user(session)
        author = create_test_user(session)
        post = create_test_post(session, author.id, "Liked post")
        create_test_like(session, user.id, post_id=post.id)

        feed = get_explore_feed(session, limit=10, offset=0, user_id=user.id)
        found = next((p for p in feed if p["id"] == post.id), None)
        assert found is not None
        assert found["is_liked"] is True
