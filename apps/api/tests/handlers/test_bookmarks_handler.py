"""Tests for BookmarksService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import bookmarks_pb2
from chirp_api.handlers.bookmarks_handler import BookmarksServiceServicer


@pytest.fixture
def servicer():
    return BookmarksServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestBookmarksHandler:
    @patch("chirp_api.handlers.bookmarks_handler.toggle_bookmark")
    @patch("chirp_api.handlers.bookmarks_handler.validate_session_token")
    @patch("chirp_api.handlers.bookmarks_handler.SessionLocal")
    def test_toggle_bookmark(
        self, mock_session_cls, mock_validate, mock_toggle, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_toggle.return_value = {"bookmarked": True}

        request = bookmarks_pb2.ToggleBookmarkRequest(
            post_id="post-123",
            session_token="valid-token",
        )

        response = servicer.ToggleBookmark(request, context)
        assert response.success is True
        assert response.bookmarked is True

    @patch("chirp_api.handlers.bookmarks_handler.get_bookmark_status")
    @patch("chirp_api.handlers.bookmarks_handler.validate_session_token")
    @patch("chirp_api.handlers.bookmarks_handler.SessionLocal")
    def test_get_bookmark_status(
        self, mock_session_cls, mock_validate, mock_status, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_status.return_value = {"bookmarked": True}

        request = bookmarks_pb2.GetBookmarkStatusRequest(
            post_id="post-123",
            session_token="valid-token",
        )

        response = servicer.GetBookmarkStatus(request, context)
        assert response.bookmarked is True

    @patch("chirp_api.handlers.bookmarks_handler.get_bookmarked_posts")
    @patch("chirp_api.handlers.bookmarks_handler.validate_session_token")
    @patch("chirp_api.handlers.bookmarks_handler.SessionLocal")
    def test_get_bookmarked_posts(
        self, mock_session_cls, mock_validate, mock_posts, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_posts.return_value = [
            {
                "id": "post-1",
                "content": "Bookmarked content",
                "created_at": 1700000000,
                "updated_at": 1700000000,
                "author": {
                    "id": "u-1",
                    "username": "author1",
                    "display_name": "Author 1",
                    "avatar_url": "",
                },
                "like_count": 5,
                "comment_count": 2,
                "is_liked": False,
            }
        ]

        request = bookmarks_pb2.GetBookmarkedPostsRequest(
            session_token="valid-token",
            limit=10,
            offset=0,
        )

        response = servicer.GetBookmarkedPosts(request, context)
        assert len(response.posts) == 1
        assert response.posts[0].id == "post-1"
