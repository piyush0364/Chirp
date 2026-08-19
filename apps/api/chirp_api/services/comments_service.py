"""Comments service for Chirp API."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Post, User
from chirp_api.services.mentions_service import process_mentions
from chirp_api.services.notifications_service import create_notification
from chirp_api.services.query_helpers import batch_get_comment_enrichment
from chirp_api.services.utils import generate_id


def _get_comment_like_info(session: Session, comment_id: str, user_id: str | None = None) -> dict:
    """Get like count and user like status for a single comment.

    Retained for backward compatibility. Uses batch helper.
    """
    enrichment = batch_get_comment_enrichment(session, [comment_id], user_id)
    return enrichment.get(comment_id, {"like_count": 0, "is_liked": False})


def create_comment(
    session: Session,
    post_id: str,
    content: str,
    author_id: str,
    parent_id: str | None = None,
) -> dict:
    """Create a new comment on a post.

    Returns dict with comment_id.
    Raises Exception if content empty, post not found, parent invalid, or nesting too deep.
    """
    if not content or len(content) == 0:
        raise Exception("Comment content is required")

    # Verify post exists
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    # If parentId provided, verify parent comment exists
    if parent_id:
        parent_comment = session.execute(
            select(Comment).where(Comment.id == parent_id)
        ).scalar_one_or_none()

        if not parent_comment:
            raise Exception("Parent comment not found")

        # Only allow one level of nesting
        if parent_comment.parent_id:
            raise Exception("Cannot reply to a reply")

    comment_id = generate_id()
    comment = Comment(
        id=comment_id,
        content=content,
        post_id=post_id,
        author_id=author_id,
        parent_id=parent_id or None,
    )
    session.add(comment)
    session.commit()

    # Create notification for post author
    create_notification(
        session,
        user_id=post.author_id,
        notification_type="comment",
        actor_id=author_id,
        post_id=post_id,
        comment_id=comment_id,
    )

    # Process mentions and create notifications
    process_mentions(session, content, author_id, post_id, comment_id)

    return {"comment_id": comment_id}


def get_post_comments(session: Session, post_id: str, user_id: str | None = None) -> list:
    """Get all comments for a post, with nested replies and like info in O(1) database queries.

    Returns list of comment dicts with nested replies.
    """
    # Fetch all comments and authors for this post in a single query
    all_comments = session.execute(
        select(Comment, User)
        .outerjoin(User, Comment.author_id == User.id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    ).all()

    if not all_comments:
        return []

    comment_ids = [c.id for c, _ in all_comments]
    enrichment = batch_get_comment_enrichment(session, comment_ids, user_id)

    top_level_comments = []
    replies_by_parent: dict[str, list[dict]] = {}

    # First pass: Build comment objects and group replies
    for comment, author in all_comments:
        like_info = enrichment.get(comment.id, {"like_count": 0, "is_liked": False})
        comment_dict = {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "parent_id": comment.parent_id,
            "author": {
                "id": author.id if author else None,
                "username": author.username if author else None,
                "display_name": author.display_name if author else None,
                "avatar_url": author.avatar_url if author else None,
            },
            "like_count": like_info.get("like_count", 0),
            "is_liked": like_info.get("is_liked", False),
            "replies": [],
        }

        if comment.parent_id:
            replies_by_parent.setdefault(comment.parent_id, []).append(comment_dict)
        else:
            top_level_comments.append(comment_dict)

    # Second pass: Attach replies to their parent comments
    for top_comment in top_level_comments:
        top_comment["replies"] = replies_by_parent.get(top_comment["id"], [])

    return top_level_comments


def delete_comment(session: Session, comment_id: str, user_id: str) -> dict:
    """Delete a comment.

    Returns dict with success boolean.
    Raises Exception if comment not found or not owned by user.
    """
    comment = session.execute(select(Comment).where(Comment.id == comment_id)).scalar_one_or_none()

    if not comment:
        raise Exception("Comment not found")

    if comment.author_id != user_id:
        raise Exception("You can only delete your own comments")

    session.delete(comment)
    session.commit()

    return {"success": True}
