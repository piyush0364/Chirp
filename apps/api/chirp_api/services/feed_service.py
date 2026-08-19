"""Feed service for Chirp API."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Follow, Post, User
from chirp_api.services.query_helpers import (
    batch_get_post_enrichment,
    format_post_dict,
)


def _get_post_counts(session: Session, post_id: str, user_id: str | None = None) -> dict:
    """Get like count, comment count, and user like status for a single post.

    Retained for backward compatibility. Uses batch helper under the hood.
    """
    enrichment = batch_get_post_enrichment(session, [post_id], user_id)
    return enrichment.get(post_id, {"like_count": 0, "comment_count": 0, "is_liked": False})


def get_home_feed(
    session: Session,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Get home feed: posts from followed users + own posts.

    Returns list of post dicts in O(1) database queries.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    # Get users that the current user follows
    following = (
        session.execute(select(Follow.following_id).where(Follow.follower_id == user_id))
        .scalars()
        .all()
    )

    following_ids = list(following)

    # Include the user's own posts as well
    user_ids = [*following_ids, user_id]

    if len(user_ids) == 0:
        return []

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.author_id.in_(user_ids))
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    enrichment = batch_get_post_enrichment(session, post_ids, user_id)

    return [format_post_dict(post, author, enrichment.get(post.id, {})) for post, author in results]


def get_explore_feed(
    session: Session,
    limit: int = 20,
    offset: int = 0,
    user_id: str | None = None,
) -> list:
    """Get explore feed: all posts ordered by recency.

    Returns list of post dicts in O(1) database queries.
    """
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    enrichment = batch_get_post_enrichment(session, post_ids, user_id)

    return [format_post_dict(post, author, enrichment.get(post.id, {})) for post, author in results]
