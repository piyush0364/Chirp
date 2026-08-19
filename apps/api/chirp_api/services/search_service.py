"""Search service for Chirp API."""

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Post, User
from chirp_api.services.query_helpers import (
    batch_get_post_enrichment,
    format_post_dict,
)


def _get_post_counts(session: Session, post_id: str, user_id: str | None = None) -> dict:
    """Get like count, comment count, and user like status for a single post.

    Retained for backward compatibility. Uses batch helper.
    """
    enrichment = batch_get_post_enrichment(session, [post_id], user_id)
    return enrichment.get(post_id, {"like_count": 0, "comment_count": 0, "is_liked": False})


def search_posts(session: Session, query: str, user_id: str | None = None) -> list:
    """Search posts by content with LIKE pattern in O(1) database queries.

    Returns list of post dicts. Returns empty list if query is empty.
    """
    if not query or len(query.strip()) == 0:
        return []

    search_pattern = f"%{query}%"

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.content.like(search_pattern))
        .order_by(desc(Post.created_at))
        .limit(50)
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    enrichment = batch_get_post_enrichment(session, post_ids, user_id)

    return [format_post_dict(post, author, enrichment.get(post.id, {})) for post, author in results]


def search_users(session: Session, query: str) -> list:
    """Search users by username or display name with LIKE pattern.

    Returns list of user dicts. Returns empty list if query is empty.
    """
    if not query or len(query.strip()) == 0:
        return []

    search_pattern = f"%{query}%"

    results = (
        session.execute(
            select(User)
            .where(
                or_(
                    User.username.like(search_pattern),
                    User.display_name.like(search_pattern),
                )
            )
            .limit(20)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
        }
        for user in results
    ]
