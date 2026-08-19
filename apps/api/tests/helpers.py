"""Test data creation helpers for Chirp API tests.

Provides factory functions for creating test entities in the database.
Each helper uses generate_id() and hash_password() with unique tokens to ensure total test
isolation.
"""

import uuid

from sqlalchemy.orm import Session

from chirp_api.db.models import (
    AuditLog,
    Bookmark,
    Comment,
    Follow,
    Like,
    Notification,
    Post,
    Report,
    User,
)
from chirp_api.services.utils import generate_id, hash_password


def create_test_user(session: Session, overrides: dict | None = None) -> User:
    """Create a test user with sensible defaults.

    Returns the created User ORM object.
    """
    unique_token = uuid.uuid4().hex[:8]
    defaults = {
        "id": generate_id(),
        "email": f"test-{unique_token}@example.com",
        "username": f"user-{unique_token}",
        "display_name": f"Test User {unique_token}",
        "password_hash": hash_password("password123"),
        "role": "user",
    }
    if overrides:
        defaults.update(overrides)

    user = User(**defaults)
    session.add(user)
    session.commit()
    return user


def create_test_post(session: Session, author_id: str, content: str = "Test post") -> Post:
    """Create a test post.

    Returns the created Post ORM object.
    """
    post = Post(
        id=generate_id(),
        content=content,
        author_id=author_id,
    )
    session.add(post)
    session.commit()
    return post


def create_test_comment(
    session: Session,
    post_id: str,
    author_id: str,
    content: str = "Test comment",
    parent_id: str | None = None,
) -> Comment:
    """Create a test comment.

    Returns the created Comment ORM object.
    """
    comment = Comment(
        id=generate_id(),
        content=content,
        post_id=post_id,
        author_id=author_id,
        parent_id=parent_id,
    )
    session.add(comment)
    session.commit()
    return comment


def create_test_like(
    session: Session,
    user_id: str,
    post_id: str | None = None,
    comment_id: str | None = None,
) -> Like:
    """Create a test like (on a post or comment).

    Returns the created Like ORM object.
    """
    like = Like(
        id=generate_id(),
        user_id=user_id,
        post_id=post_id,
        comment_id=comment_id,
    )
    session.add(like)
    session.commit()
    return like


def create_test_follow(session: Session, follower_id: str, following_id: str) -> Follow:
    """Create a test follow relationship.

    Returns the created Follow ORM object.
    """
    follow = Follow(
        id=generate_id(),
        follower_id=follower_id,
        following_id=following_id,
    )
    session.add(follow)
    session.commit()
    return follow


def create_test_bookmark(session: Session, user_id: str, post_id: str) -> Bookmark:
    """Create a test bookmark.

    Returns the created Bookmark ORM object.
    """
    bookmark = Bookmark(
        id=generate_id(),
        user_id=user_id,
        post_id=post_id,
    )
    session.add(bookmark)
    session.commit()
    return bookmark


def create_test_notification(
    session: Session,
    user_id: str,
    actor_id: str,
    type: str = "like",
    post_id: str | None = None,
    comment_id: str | None = None,
    read: bool = False,
) -> Notification:
    """Create a test notification.

    Returns the created Notification ORM object.
    """
    notification = Notification(
        id=generate_id(),
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        post_id=post_id,
        comment_id=comment_id,
        read=read,
    )
    session.add(notification)
    session.commit()
    return notification


def create_test_report(
    session: Session,
    reporter_id: str,
    target_type: str = "post",
    target_id: str = "target-123",
    reason: str = "spam",
    description: str | None = "Spam content",
    status: str = "pending",
) -> Report:
    """Create a test report.

    Returns the created Report ORM object.
    """
    report = Report(
        id=generate_id(),
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description,
        status=status,
    )
    session.add(report)
    session.commit()
    return report


def create_test_audit_log(
    session: Session,
    admin_id: str,
    action: str = "ban_user",
    target_type: str | None = "user",
    target_id: str | None = "target-123",
    details: str | None = "Violated terms",
    ip_address: str | None = "127.0.0.1",
) -> AuditLog:
    """Create a test audit log.

    Returns the created AuditLog ORM object.
    """
    audit_log = AuditLog(
        id=generate_id(),
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    session.add(audit_log)
    session.commit()
    return audit_log
