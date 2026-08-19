"""Reusable batch query and hydration helpers for Chirp API services.

Prevents N+1 query patterns by executing set-based GROUP BY aggregations
and batch lookups in O(1) database round trips.
"""

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like, Post, User


def batch_get_post_enrichment(
    session: Session,
    post_ids: list[str],
    user_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Fetch like count, comment count, and user like status for a list of post IDs in batch.

    Executes at most 2-3 fixed queries total regardless of how many post IDs are passed.
    Returns a dict mapping post_id -> {"like_count": int, "comment_count": int, "is_liked": bool}.
    """
    if not post_ids:
        return {}

    # Initialize default counts for all requested posts
    enrichment: dict[str, dict[str, Any]] = {
        pid: {"like_count": 0, "comment_count": 0, "is_liked": False} for pid in post_ids
    }

    # Batch Query 1: Like counts per post
    like_counts = session.execute(
        select(Like.post_id, func.count())
        .where(Like.post_id.in_(post_ids))
        .group_by(Like.post_id)
    ).all()
    for pid, count in like_counts:
        if pid in enrichment:
            enrichment[pid]["like_count"] = count or 0

    # Batch Query 2: Comment counts per post
    comment_counts = session.execute(
        select(Comment.post_id, func.count())
        .where(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
    ).all()
    for pid, count in comment_counts:
        if pid in enrichment:
            enrichment[pid]["comment_count"] = count or 0

    # Batch Query 3: User like statuses for requested posts
    if user_id:
        liked_post_ids = set(
            session.execute(
                select(Like.post_id).where(
                    and_(Like.post_id.in_(post_ids), Like.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        for pid in liked_post_ids:
            if pid in enrichment:
                enrichment[pid]["is_liked"] = True

    return enrichment


def batch_get_comment_enrichment(
    session: Session,
    comment_ids: list[str],
    user_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Fetch like count and user like status for a list of comment IDs in batch.

    Executes at most 1-2 fixed queries total regardless of how many comment IDs are passed.
    Returns a dict mapping comment_id -> {"like_count": int, "is_liked": bool}.
    """
    if not comment_ids:
        return {}

    enrichment: dict[str, dict[str, Any]] = {
        cid: {"like_count": 0, "is_liked": False} for cid in comment_ids
    }

    # Batch Query 1: Like counts per comment
    like_counts = session.execute(
        select(Like.comment_id, func.count())
        .where(Like.comment_id.in_(comment_ids))
        .group_by(Like.comment_id)
    ).all()
    for cid, count in like_counts:
        if cid in enrichment:
            enrichment[cid]["like_count"] = count or 0

    # Batch Query 2: User like status for requested comments
    if user_id:
        liked_comment_ids = set(
            session.execute(
                select(Like.comment_id).where(
                    and_(Like.comment_id.in_(comment_ids), Like.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        for cid in liked_comment_ids:
            if cid in enrichment:
                enrichment[cid]["is_liked"] = True

    return enrichment


def batch_get_user_counts(
    session: Session,
    user_ids: list[str],
) -> dict[str, dict[str, int]]:
    """Fetch post count and comment count for a list of user IDs in batch.

    Returns a dict mapping user_id -> {"post_count": int, "comment_count": int}.
    """
    if not user_ids:
        return {}

    counts: dict[str, dict[str, int]] = {
        uid: {"post_count": 0, "comment_count": 0} for uid in user_ids
    }

    # Post counts
    post_counts = session.execute(
        select(Post.author_id, func.count())
        .where(Post.author_id.in_(user_ids))
        .group_by(Post.author_id)
    ).all()
    for uid, count in post_counts:
        if uid in counts:
            counts[uid]["post_count"] = count or 0

    # Comment counts
    comment_counts = session.execute(
        select(Comment.author_id, func.count())
        .where(Comment.author_id.in_(user_ids))
        .group_by(Comment.author_id)
    ).all()
    for uid, count in comment_counts:
        if uid in counts:
            counts[uid]["comment_count"] = count or 0

    return counts


def format_post_dict(post: Post, author: User | None, enrichment: dict[str, Any]) -> dict[str, Any]:
    """Format a post entity, author, and enrichment dictionary into the canonical response dict."""
    return {
        "id": post.id,
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author": {
            "id": author.id if author else None,
            "username": author.username if author else None,
            "display_name": author.display_name if author else None,
            "avatar_url": author.avatar_url if author else None,
        },
        "like_count": enrichment.get("like_count", 0),
        "comment_count": enrichment.get("comment_count", 0),
        "is_liked": enrichment.get("is_liked", False),
    }
