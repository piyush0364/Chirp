"""Tests for FeedService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import feed_pb2
from chirp_api.handlers.feed_handler import FeedServiceServicer


@pytest.fixture
def servicer():
    return FeedServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestFeedHandler:
    @patch("chirp_api.handlers.feed_handler.get_home_feed")
    @patch("chirp_api.handlers.feed_handler.validate_session_token")
    @patch("chirp_api.handlers.feed_handler.SessionLocal")
    def test_get_home_feed(
        self, mock_session_cls, mock_validate, mock_feed, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_feed.return_value = [
            {
                "id": "post-1",
                "content": "Feed post",
                "created_at": 1700000000,
                "updated_at": 1700000000,
                "author": {
                    "id": "u-1",
                    "username": "author1",
                    "display_name": "Author 1",
                    "avatar_url": "",
                },
                "like_count": 10,
                "comment_count": 3,
                "is_liked": True,
            }
        ]

        request = feed_pb2.GetHomeFeedRequest(
            session_token="valid-token",
        )

        response = servicer.GetHomeFeed(request, context)
        assert len(response.posts) == 1
        assert response.posts[0].id == "post-1"
        assert response.posts[0].is_liked is True

    @patch("chirp_api.handlers.feed_handler.get_explore_feed")
    @patch("chirp_api.handlers.feed_handler.SessionLocal")
    def test_get_explore_feed_unauthenticated(
        self, mock_session_cls, mock_feed, servicer, context
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_feed.return_value = [
            {
                "id": "post-explore",
                "content": "Public explore post",
                "created_at": 1700000000,
                "updated_at": 1700000000,
                "author": {
                    "id": "u-2",
                    "username": "author2",
                    "display_name": "Author 2",
                    "avatar_url": "",
                },
                "like_count": 0,
                "comment_count": 0,
                "is_liked": False,
            }
        ]

        request = feed_pb2.GetExploreFeedRequest()
        response = servicer.GetExploreFeed(request, context)
        assert len(response.posts) == 1
        assert response.posts[0].id == "post-explore"
