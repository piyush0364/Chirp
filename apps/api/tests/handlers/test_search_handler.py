"""Tests for SearchService handler."""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import search_pb2
from chirp_api.handlers.search_handler import SearchServiceServicer


@pytest.fixture
def servicer():
    return SearchServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


class TestSearchHandler:
    @patch("chirp_api.handlers.search_handler.search_posts")
    @patch("chirp_api.handlers.search_handler.SessionLocal")
    def test_search_posts(self, mock_session_cls, mock_search_posts, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_search_posts.return_value = [
            {
                "id": "post-1",
                "content": "Found post",
                "created_at": 1700000000,
                "updated_at": 1700000000,
                "author": {
                    "id": "u-1",
                    "username": "author",
                    "display_name": "Author",
                    "avatar_url": "",
                },
                "like_count": 0,
                "comment_count": 0,
                "is_liked": False,
            }
        ]

        request = search_pb2.SearchRequest(query="Found")
        response = servicer.SearchPosts(request, context)
        assert len(response.posts) == 1
        assert response.posts[0].id == "post-1"

    @patch("chirp_api.handlers.search_handler.search_users")
    @patch("chirp_api.handlers.search_handler.SessionLocal")
    def test_search_users(self, mock_session_cls, mock_search_users, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_search_users.return_value = [
            {
                "id": "u-1",
                "username": "founduser",
                "display_name": "Found User",
                "avatar_url": "",
                "bio": "",
            }
        ]

        request = search_pb2.SearchRequest(query="founduser")
        response = servicer.SearchUsers(request, context)
        assert len(response.users) == 1
        assert response.users[0].username == "founduser"
