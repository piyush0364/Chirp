import asyncio
from typing import Any, Awaitable, Callable, cast
from unittest.mock import AsyncMock, MagicMock

import grpc

from chirp_api.middleware.api_key_interceptor import API_KEY, APIKeyInterceptor


def test_api_key_interceptor_valid_key():
    async def run_test():
        interceptor = APIKeyInterceptor()

        continuation = AsyncMock(return_value="success")
        handler_call_details = MagicMock()
        handler_call_details.invocation_metadata = (
            ("x-api-key", API_KEY),
        )

        result = await interceptor.intercept_service(continuation, handler_call_details)
        assert result == "success"
        continuation.assert_called_once_with(handler_call_details)
    asyncio.run(run_test())

def test_api_key_interceptor_invalid_key():
    async def run_test():
        interceptor = APIKeyInterceptor()

        continuation = AsyncMock()
        handler_call_details = MagicMock()
        handler_call_details.invocation_metadata = (
            ("x-api-key", "wrong-key"),
        )

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # The result should be a grpc method handler that aborts
        assert result is not None
        assert callable(result.unary_unary)

        # Test that the returned handler aborts
        mock_request = MagicMock()
        mock_context = AsyncMock()

        assert result.unary_unary is not None
        handler = cast(Callable[[Any, Any], Awaitable[Any]], result.unary_unary)
        await handler(mock_request, mock_context)

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing API key"
        )
    asyncio.run(run_test())

def test_api_key_interceptor_missing_key():
    async def run_test():
        interceptor = APIKeyInterceptor()

        continuation = AsyncMock()
        handler_call_details = MagicMock()
        handler_call_details.invocation_metadata = ()

        result = await interceptor.intercept_service(continuation, handler_call_details)

        # The result should be a grpc method handler that aborts
        assert result is not None
        assert callable(result.unary_unary)

        # Test that the returned handler aborts
        mock_request = MagicMock()
        mock_context = AsyncMock()

        assert result.unary_unary is not None
        handler = cast(Callable[[Any, Any], Awaitable[Any]], result.unary_unary)
        await handler(mock_request, mock_context)

        mock_context.abort.assert_called_once_with(
            grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing API key"
        )
    asyncio.run(run_test())
