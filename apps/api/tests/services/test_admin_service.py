"""Unit tests for Admin Service."""

import pytest

from chirp_api.services.admin_service import (
    ban_user,
    delete_comment_admin,
    delete_post_admin,
    delete_user,
    get_audit_logs,
    get_dashboard_stats,
    get_report,
    get_user_details,
    list_users,
    review_report,
    unban_user,
    update_user_role,
)
from tests.helpers import (
    create_test_audit_log,
    create_test_comment,
    create_test_post,
    create_test_report,
    create_test_user,
)


class TestAdminService:
    def test_list_and_get_user_details(self, session):
        create_test_user(session, {"role": "admin"})
        target = create_test_user(session, {"role": "user"})

        users_list = list_users(session, limit=10, offset=0)
        assert users_list["total"] >= 2

        details = get_user_details(session, target.id)
        assert details["id"] == target.id
        assert details["role"] == "user"

    def test_ban_and_unban_user(self, session):
        admin = create_test_user(session, {"role": "admin"})
        target = create_test_user(session)

        ban_res = ban_user(session, target.id, "Violation of rules", admin.id)
        assert ban_res["success"] is True

        user_details = get_user_details(session, target.id)
        assert user_details["banned_at"] is not None
        assert user_details["banned_reason"] == "Violation of rules"

        unban_res = unban_user(session, target.id, admin.id)
        assert unban_res["success"] is True

        user_details_after = get_user_details(session, target.id)
        assert user_details_after["banned_at"] is None

    def test_cannot_ban_super_admin(self, session):
        admin = create_test_user(session, {"role": "admin"})
        super_admin = create_test_user(session, {"role": "admin"})

        with pytest.raises(Exception, match="Cannot ban admin users"):
            ban_user(session, super_admin.id, "Reason", admin.id)

    def test_update_user_role_and_delete(self, session):
        admin = create_test_user(session, {"role": "admin"})
        target = create_test_user(session, {"role": "user"})

        update_user_role(session, target.id, "moderator", admin.id)
        details = get_user_details(session, target.id)
        assert details["role"] == "moderator"

        del_res = delete_user(session, target.id, admin.id)
        assert del_res["success"] is True

        with pytest.raises(Exception, match="User not found"):
            get_user_details(session, target.id)

    def test_delete_post_and_comment_admin(self, session):
        admin = create_test_user(session, {"role": "admin"})
        user = create_test_user(session)
        post = create_test_post(session, user.id, "Spam post")
        comment = create_test_comment(session, post.id, user.id, "Spam comment")

        del_comment = delete_comment_admin(session, comment.id, "Inappropriate", admin.id)
        assert del_comment["success"] is True

        del_post = delete_post_admin(session, post.id, "Spam", admin.id)
        assert del_post["success"] is True

    def test_reports_workflow(self, session):
        admin = create_test_user(session, {"role": "admin"})
        reporter = create_test_user(session)
        target_user = create_test_user(session)

        report = create_test_report(
            session, reporter.id, target_type="user", target_id=target_user.id
        )

        rep_details = get_report(session, report.id)
        assert rep_details["id"] == report.id
        assert rep_details["status"] == "pending"

        rev_res = review_report(
            session, report.id, action="ban", admin_id=admin.id, notes="Banned user"
        )
        assert rev_res["success"] is True

        rep_after = get_report(session, report.id)
        assert rep_after["status"] == "reviewed"

    def test_dashboard_stats_and_audit_logs(self, session):
        admin = create_test_user(session, {"role": "admin"})
        create_test_audit_log(session, admin.id, action="ban_user")

        stats = get_dashboard_stats(session)
        assert "total_users" in stats
        assert "total_posts" in stats

        logs = get_audit_logs(session)
        assert logs["total"] >= 1
        assert logs["logs"][0]["action"] == "ban_user"
