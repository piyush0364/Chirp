"""Automated query budget tests for Chirp API services.

Ensures that N+1 query regressions cannot be reintroduced into the codebase.
"""

import pytest
from sqlalchemy import event

from chirp_api.db.models import Bookmark, Comment, Follow, Like, Post, User
from chirp_api.services.bookmarks_service import get_bookmarked_posts
from chirp_api.services.comments_service import get_post_comments
from chirp_api.services.feed_service import get_explore_feed, get_home_feed
from chirp_api.services.posts_service import get_posts
from chirp_api.services.users_service import get_user
from chirp_api.services.utils import generate_id, hash_password


class QueryCounter:
    def __init__(self, session):
        self.engine = session.get_bind()
        self.queries: list[str] = []

    def __enter__(self):
        self.queries = []
        event.listen(self.engine, "before_cursor_execute", self._before_cursor_execute)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(self.engine, "before_cursor_execute", self._before_cursor_execute)

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.queries.append(statement)

    @property
    def count(self) -> int:
        return len(self.queries)


@pytest.fixture
def populated_db(session):
    """Seed test database with users, posts, comments, likes, follows, and bookmarks."""
    users = []
    for i in range(5):
        u = User(
            id=generate_id(),
            email=f"user{i}@test.com",
            username=f"user_{i}",
            display_name=f"User {i}",
            password_hash=hash_password("pw"),
        )
        session.add(u)
        users.append(u)
    session.commit()

    u0, u1 = users[0], users[1]

    # u0 follows u1 and others
    for u in users[1:]:
        f = Follow(id=generate_id(), follower_id=u0.id, following_id=u.id)
        session.add(f)
    session.commit()

    # Create 15 posts by u1
    posts = []
    for i in range(15):
        p = Post(id=generate_id(), content=f"Post content {i}", author_id=u1.id)
        session.add(p)
        posts.append(p)
    session.commit()

    # Add comments, likes, and bookmarks on posts
    for p in posts:
        b = Bookmark(id=generate_id(), user_id=u0.id, post_id=p.id)
        l0 = Like(id=generate_id(), user_id=u0.id, post_id=p.id)
        l1 = Like(id=generate_id(), user_id=u1.id, post_id=p.id)
        c0 = Comment(id=generate_id(), content="Top comment", post_id=p.id, author_id=u0.id)
        session.add_all([b, l0, l1, c0])
    session.commit()

    # Add nested replies on post[0]
    p0 = posts[0]
    c_parent = session.query(Comment).filter(Comment.post_id == p0.id).first()
    for i in range(5):
        c_reply = Comment(
            id=generate_id(),
            content=f"Reply {i}",
            post_id=p0.id,
            author_id=u1.id,
            parent_id=c_parent.id,
        )
        session.add(c_reply)
    session.commit()

    return {
        "users": users,
        "posts": posts,
        "current_user": u0,
        "target_user": u1,
    }


def test_home_feed_query_budget(session, populated_db):
    """Loading home feed of 10 posts must not exceed 5 SQL queries (constant O(1))."""
    u0 = populated_db["current_user"]

    with QueryCounter(session) as qc:
        feed = get_home_feed(session, user_id=u0.id, limit=10)

    assert len(feed) == 10
    assert qc.count <= 5, f"Expected <= 5 queries for home feed, got {qc.count}"


def test_user_profile_query_budget(session, populated_db):
    """Loading user profile must execute in exactly 1 SQL query."""
    u0 = populated_db["current_user"]
    u1 = populated_db["target_user"]

    with QueryCounter(session) as qc:
        profile = get_user(session, username=u1.username, requester_id=u0.id)

    assert profile["username"] == u1.username
    assert profile["is_following"] is True
    assert profile["follower_count"] >= 1
    assert profile["post_count"] == 15
    assert qc.count <= 1, f"Expected <= 1 query for user profile, got {qc.count}"


def test_bookmarks_query_budget(session, populated_db):
    """Loading bookmarks page of 10 posts must not exceed 4 SQL queries."""
    u0 = populated_db["current_user"]

    with QueryCounter(session) as qc:
        bookmarks = get_bookmarked_posts(session, user_id=u0.id, requester_id=u0.id, limit=10)

    assert len(bookmarks) == 10
    assert bookmarks[0]["is_liked"] is True
    assert qc.count <= 4, f"Expected <= 4 queries for bookmarks page, got {qc.count}"


def test_post_comments_nested_query_budget(session, populated_db):
    """Loading comments with nested replies must execute in <= 3 SQL queries."""
    p0 = populated_db["posts"][0]
    u0 = populated_db["current_user"]

    with QueryCounter(session) as qc:
        comments = get_post_comments(session, post_id=p0.id, user_id=u0.id)

    assert len(comments) >= 1
    assert len(comments[0]["replies"]) == 5
    assert qc.count <= 3, f"Expected <= 3 queries for post comments, got {qc.count}"


def test_explore_feed_query_budget(session, populated_db):
    """Loading explore feed must execute in <= 4 SQL queries."""
    u0 = populated_db["current_user"]

    with QueryCounter(session) as qc:
        posts = get_explore_feed(session, limit=10, user_id=u0.id)

    assert len(posts) == 10
    assert qc.count <= 4, f"Expected <= 4 queries for explore feed, got {qc.count}"


def test_get_posts_query_budget(session, populated_db):
    """Loading public posts list must execute in <= 4 SQL queries."""
    u0 = populated_db["current_user"]

    with QueryCounter(session) as qc:
        posts = get_posts(session, limit=10, user_id=u0.id)

    assert len(posts) == 10
    assert qc.count <= 4, f"Expected <= 4 queries for get_posts, got {qc.count}"
