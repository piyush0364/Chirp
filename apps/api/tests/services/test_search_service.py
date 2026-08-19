"""Unit tests for Search Service."""

from chirp_api.services.search_service import search_posts, search_users
from tests.helpers import create_test_post, create_test_user


class TestSearchService:
    def test_search_posts(self, session):
        user = create_test_user(session)
        p1 = create_test_post(session, user.id, "Learning python is amazing")
        create_test_post(session, user.id, "TypeScript and React are cool")

        results = search_posts(session, "python")
        assert len(results) == 1
        assert results[0]["id"] == p1.id
        assert results[0]["author"]["username"] == user.username

    def test_search_posts_empty_query(self, session):
        user = create_test_user(session)
        create_test_post(session, user.id, "Hello")

        assert search_posts(session, "") == []
        assert search_posts(session, "   ") == []

    def test_search_users(self, session):
        u1 = create_test_user(session, {"username": "superstar", "display_name": "Famous Singer"})
        u2 = create_test_user(session, {"username": "ordinary", "display_name": "Super Fan"})

        results_username = search_users(session, "superstar")
        assert any(u["id"] == u1.id for u in results_username)

        results_display = search_users(session, "Fan")
        assert any(u["id"] == u2.id for u in results_display)

    def test_search_users_empty_query(self, session):
        create_test_user(session)
        assert search_users(session, "") == []
