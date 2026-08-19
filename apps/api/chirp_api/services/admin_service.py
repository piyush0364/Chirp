"""Admin service for Chirp API."""

import json
import time

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from chirp_api.db.models import AuditLog, Comment, Post, Report, User
from chirp_api.services.query_helpers import batch_get_user_counts
from chirp_api.services.utils import generate_id


def _create_audit_log(
    session: Session,
    admin_id: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Create an audit log entry."""
    audit_log = AuditLog(
        id=generate_id(),
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
    )
    session.add(audit_log)
    session.commit()


def list_users(
    session: Session,
    limit: int = 20,
    offset: int = 0,
    search_query: str | None = None,
    role_filter: str | None = None,
) -> dict:
    """List users with pagination and optional filters in O(1) database queries.

    Returns dict with users list and total count.
    """
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    query = select(User)

    if search_query:
        pattern = f"%{search_query}%"
        query = query.where(
            or_(
                User.username.like(pattern),
                User.display_name.like(pattern),
                User.email.like(pattern),
            )
        )

    if role_filter:
        query = query.where(User.role == role_filter)

    results = (
        session.execute(query.order_by(desc(User.created_at)).limit(limit).offset(offset))
        .scalars()
        .all()
    )

    user_ids = [user.id for user in results]
    user_counts = batch_get_user_counts(session, user_ids)

    users_with_counts = []
    for user in results:
        counts = user_counts.get(user.id, {"post_count": 0, "comment_count": 0})
        users_with_counts.append(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "role": user.role,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "banned_at": user.banned_at,
                "banned_reason": user.banned_reason,
                "post_count": counts.get("post_count", 0),
                "comment_count": counts.get("comment_count", 0),
            }
        )

    # Get total count (with same filters applied)
    count_query = select(func.count()).select_from(User)
    if search_query:
        pattern = f"%{search_query}%"
        count_query = count_query.where(
            or_(
                User.username.like(pattern),
                User.display_name.like(pattern),
                User.email.like(pattern),
            )
        )
    if role_filter:
        count_query = count_query.where(User.role == role_filter)
    total = session.execute(count_query).scalar() or 0

    return {
        "users": users_with_counts,
        "total": total,
    }


def get_user_details(session: Session, user_id: str) -> dict:
    """Get detailed user info for admin view in O(1) database queries.

    Returns dict with user fields and counts.
    Raises Exception if user not found.
    """
    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    user_counts = batch_get_user_counts(session, [user_id])
    counts = user_counts.get(user_id, {"post_count": 0, "comment_count": 0})

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "banned_at": user.banned_at,
        "banned_reason": user.banned_reason,
        "banned_by": user.banned_by,
        "post_count": counts.get("post_count", 0),
        "comment_count": counts.get("comment_count", 0),
    }


def ban_user(session: Session, user_id: str, reason: str, admin_id: str) -> dict:
    """Ban a user.

    Returns dict with success boolean.
    Raises Exception if user not found or is an admin.
    """
    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    if user.role == "admin":
        raise Exception("Cannot ban admin users")

    user.banned_at = int(time.time())
    user.banned_reason = reason
    user.banned_by = admin_id
    session.commit()

    # Create audit log
    _create_audit_log(session, admin_id, "ban_user", "user", user_id, {"reason": reason})

    return {"success": True}


def unban_user(session: Session, user_id: str, admin_id: str) -> dict:
    """Unban a user.

    Returns dict with success boolean.
    Raises Exception if user not found.
    """
    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    user.banned_at = None
    user.banned_reason = None
    user.banned_by = None
    session.commit()

    # Create audit log
    _create_audit_log(session, admin_id, "unban_user", "user", user_id)

    return {"success": True}


def update_user_role(session: Session, user_id: str, role: str, admin_id: str) -> dict:
    """Update a user's role.

    Returns dict with success boolean.
    Raises Exception if invalid role or user not found.
    """
    valid_roles = ["user", "admin", "moderator"]
    if role not in valid_roles:
        raise Exception("Invalid role")

    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    old_role = user.role
    user.role = role
    session.commit()

    # Create audit log
    _create_audit_log(
        session,
        admin_id,
        "update_role",
        "user",
        user_id,
        {
            "oldRole": old_role,
            "newRole": role,
        },
    )

    return {"success": True}


def delete_user(session: Session, user_id: str, admin_id: str) -> dict:
    """Delete a user.

    Returns dict with success boolean.
    Raises Exception if user not found or is an admin.
    """
    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    if user.role == "admin":
        raise Exception("Cannot delete admin users")

    username = user.username
    session.delete(user)
    session.commit()

    # Create audit log
    _create_audit_log(session, admin_id, "delete_user", "user", user_id, {"username": username})

    return {"success": True}


def delete_post_admin(session: Session, post_id: str, reason: str, admin_id: str) -> dict:
    """Admin delete a post.

    Returns dict with success boolean.
    Raises Exception if post not found.
    """
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    session.delete(post)
    session.commit()

    # Create audit log
    _create_audit_log(session, admin_id, "delete_post", "post", post_id, {"reason": reason})

    return {"success": True}


def delete_comment_admin(session: Session, comment_id: str, reason: str, admin_id: str) -> dict:
    """Admin delete a comment.

    Returns dict with success boolean.
    Raises Exception if comment not found.
    """
    comment = session.execute(select(Comment).where(Comment.id == comment_id)).scalar_one_or_none()

    if not comment:
        raise Exception("Comment not found")

    session.delete(comment)
    session.commit()

    # Create audit log
    _create_audit_log(
        session, admin_id, "delete_comment", "comment", comment_id, {"reason": reason}
    )

    return {"success": True}


def list_reports(
    session: Session,
    limit: int = 20,
    offset: int = 0,
    status_filter: str | None = None,
    type_filter: str | None = None,
) -> dict:
    """List reports with pagination and optional filters in O(1) database queries.

    Returns dict with reports list and total count.
    """
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    query = select(Report, User.username).outerjoin(User, Report.reporter_id == User.id)

    if status_filter:
        query = query.where(Report.status == status_filter)

    if type_filter:
        query = query.where(Report.target_type == type_filter)

    results = session.execute(
        query.order_by(desc(Report.created_at)).limit(limit).offset(offset)
    ).all()

    reports_with_usernames = [
        {
            "id": report.id,
            "reporter_id": report.reporter_id,
            "target_type": report.target_type,
            "target_id": report.target_id,
            "reason": report.reason,
            "description": report.description,
            "status": report.status,
            "reviewed_by": report.reviewed_by,
            "reviewed_at": report.reviewed_at,
            "created_at": report.created_at,
            "reporter_username": reporter_username or "Unknown",
        }
        for report, reporter_username in results
    ]

    total = session.execute(select(func.count()).select_from(Report)).scalar() or 0

    return {
        "reports": reports_with_usernames,
        "total": total,
    }


def get_report(session: Session, report_id: str) -> dict:
    """Get a single report by ID.

    Returns dict with report fields.
    Raises Exception if report not found.
    """
    row = session.execute(
        select(Report, User.username)
        .outerjoin(User, Report.reporter_id == User.id)
        .where(Report.id == report_id)
    ).first()

    if not row:
        raise Exception("Report not found")

    report, reporter_username = row

    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "target_type": report.target_type,
        "target_id": report.target_id,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "reviewed_by": report.reviewed_by,
        "reviewed_at": report.reviewed_at,
        "created_at": report.created_at,
        "reporter_username": reporter_username or "Unknown",
    }


def review_report(
    session: Session,
    report_id: str,
    action: str,
    admin_id: str,
    notes: str | None = None,
) -> dict:
    """Review a report and update its status.

    Returns dict with success boolean.
    Raises Exception if report not found.
    """
    report = session.execute(select(Report).where(Report.id == report_id)).scalar_one_or_none()

    if not report:
        raise Exception("Report not found")

    status = "reviewed"
    if action == "dismiss":
        status = "dismissed"
    elif action in ("warn", "remove_content", "ban_user"):
        status = "actioned"

    report.status = status
    report.reviewed_by = admin_id
    report.reviewed_at = int(time.time())
    session.commit()

    # Create audit log
    _create_audit_log(
        session,
        admin_id,
        "review_report",
        "report",
        report_id,
        {
            "action": action,
            "notes": notes,
        },
    )

    return {"success": True}


def get_dashboard_stats(session: Session) -> dict:
    """Get dashboard statistics.

    Returns dict with various count stats.
    """
    total_users = session.execute(select(func.count()).select_from(User)).scalar() or 0

    total_posts = session.execute(select(func.count()).select_from(Post)).scalar() or 0

    total_comments = session.execute(select(func.count()).select_from(Comment)).scalar() or 0

    pending_reports = (
        session.execute(
            select(func.count()).select_from(Report).where(Report.status == "pending")
        ).scalar()
        or 0
    )

    banned_users = (
        session.execute(
            select(func.count()).select_from(User).where(User.banned_at.isnot(None))
        ).scalar()
        or 0
    )

    # Today's stats (unix epoch for start of today)
    today_start = int(time.time()) - (int(time.time()) % 86400)

    new_users_today = (
        session.execute(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        ).scalar()
        or 0
    )

    new_posts_today = (
        session.execute(
            select(func.count()).select_from(Post).where(Post.created_at >= today_start)
        ).scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "pending_reports": pending_reports,
        "banned_users": banned_users,
        "new_users_today": new_users_today,
        "new_posts_today": new_posts_today,
    }


def get_audit_logs(
    session: Session,
    limit: int = 50,
    offset: int = 0,
    admin_id_filter: str | None = None,
    action_filter: str | None = None,
) -> dict:
    """Get audit logs with pagination and optional filters in O(1) database queries.

    Returns dict with logs list and total count.
    """
    assert limit > 0 and limit <= 200, "Limit must be between 1 and 200"
    assert offset >= 0, "Offset must be non-negative"

    query = select(AuditLog, User.username).outerjoin(User, AuditLog.admin_id == User.id)

    if admin_id_filter:
        query = query.where(AuditLog.admin_id == admin_id_filter)

    if action_filter:
        query = query.where(AuditLog.action == action_filter)

    results = session.execute(
        query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    ).all()

    logs_with_usernames = [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
            "admin_username": admin_username or "Unknown",
        }
        for log, admin_username in results
    ]

    total = session.execute(select(func.count()).select_from(AuditLog)).scalar() or 0

    return {
        "logs": logs_with_usernames,
        "total": total,
    }
