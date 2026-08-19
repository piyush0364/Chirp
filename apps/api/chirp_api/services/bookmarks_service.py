"""Bookmarks service for Chirp API."""

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Bookmark, Post, User
from chirp_api.services.query_helpers import (
    batch_get_post_enrichment,
    format_post_dict,
)
from chirp_api.services.utils import generate_id


def toggle_bookmark(session: Session, post_id: str, user_id: str) -> dict:
    """Toggle bookmark for a post.

    Returns dict with bookmarked boolean.
    Raises Exception if post not found.
    """
    assert isinstance(post_id, str) and len(post_id) > 0, "post_id must be non-empty"
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"

    # Verify post exists
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    # Check if already bookmarked
    existing_bookmark = session.execute(
        select(Bookmark).where(and_(Bookmark.post_id == post_id, Bookmark.user_id == user_id))
    ).scalar_one_or_none()

    if existing_bookmark:
        # Remove bookmark
        session.delete(existing_bookmark)
        session.commit()
        return {"bookmarked": False}
    else:
        # Add bookmark
        bookmark = Bookmark(
            id=generate_id(),
            post_id=post_id,
            user_id=user_id,
        )
        session.add(bookmark)
        session.commit()
        return {"bookmarked": True}


def get_bookmark_status(session: Session, post_id: str, user_id: str) -> dict:
    """Check if a user has bookmarked a post.

    Returns dict with bookmarked boolean.
    """
    bookmark = session.execute(
        select(Bookmark).where(and_(Bookmark.post_id == post_id, Bookmark.user_id == user_id))
    ).scalar_one_or_none()

    return {"bookmarked": bookmark is not None}


def get_bookmarked_posts(
    session: Session,
    user_id: str,
    requester_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Get all bookmarked posts for a user with pagination.

    Returns list of post dicts in O(1) database queries.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    results = session.execute(
        select(Post, User)
        .join(Bookmark, Bookmark.post_id == Post.id)
        .outerjoin(User, Post.author_id == User.id)
        .where(Bookmark.user_id == user_id)
        .order_by(desc(Bookmark.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    enrichment = batch_get_post_enrichment(session, post_ids, requester_id)

    return [format_post_dict(post, author, enrichment.get(post.id, {})) for post, author in results]
