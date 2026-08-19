"""Unit tests for Observability, Request Tracing, and Error Taxonomy."""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock

import grpc

from chirp_api.errors import (
    AlreadyExistsError,
    AuthenticationError,
    FailedPreconditionError,
    InternalError,
    NotFoundError,
    PermissionDeniedError,
    ResourceExhaustedError,
    ValidationError,
    map_error_to_status_code,
)
from chirp_api.middleware.observability_interceptor import ObservabilityInterceptor
from chirp_api.observability import (
    StructuredJsonFormatter,
    generate_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)


def test_error_taxonomy_status_codes():
    """Verify all domain exceptions map to their canonical gRPC status codes."""
    assert ValidationError("invalid").status_code == grpc.StatusCode.INVALID_ARGUMENT
    assert AuthenticationError("unauth").status_code == grpc.StatusCode.UNAUTHENTICATED
    assert PermissionDeniedError("forbidden").status_code == grpc.StatusCode.PERMISSION_DENIED
    assert NotFoundError("missing").status_code == grpc.StatusCode.NOT_FOUND
    assert AlreadyExistsError("duplicate").status_code == grpc.StatusCode.ALREADY_EXISTS
    assert FailedPreconditionError("state").status_code == grpc.StatusCode.FAILED_PRECONDITION
    assert ResourceExhaustedError("rate limit").status_code == grpc.StatusCode.RESOURCE_EXHAUSTED
    assert InternalError("server error").status_code == grpc.StatusCode.INTERNAL


def test_error_mapping_utility():
    """Verify map_error_to_status_code handles both domain errors and standard exceptions."""
    code, msg = map_error_to_status_code(NotFoundError("User not found"))
    assert code == grpc.StatusCode.NOT_FOUND
    assert msg == "User not found"

    code, msg = map_error_to_status_code(Exception("User not found"))
    assert code == grpc.StatusCode.NOT_FOUND

    code, msg = map_error_to_status_code(Exception("Duplicate username"))
    assert code == grpc.StatusCode.ALREADY_EXISTS

    code, msg = map_error_to_status_code(Exception("Authentication required"))
    assert code == grpc.StatusCode.UNAUTHENTICATED


def test_trace_id_generation_and_context():
    """Verify trace ID generation, setting, and propagation via ContextVar."""
    tid1 = generate_trace_id()
    assert tid1.startswith("trace-")

    token = set_trace_id(tid1)
    assert get_trace_id() == tid1

    reset_trace_id(token)


def test_structured_json_formatter():
    """Verify StructuredJsonFormatter produces parseable JSON with trace context."""
    formatter = StructuredJsonFormatter()
    token = set_trace_id("trace-test-12345")

    try:
        record = logging.LogRecord(
            name="chirp_api.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="User %s logged in",
            args=("alice",),
            exc_info=None,
        )
        record.user_id = "u-123"
        record.duration_ms = 42.5

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "User alice logged in"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "chirp_api.test"
        assert parsed["trace_id"] == "trace-test-12345"
        assert parsed["user_id"] == "u-123"
        assert parsed["duration_ms"] == 42.5
        assert "timestamp" in parsed
    finally:
        reset_trace_id(token)


def test_observability_interceptor_success():
    """Verify ObservabilityInterceptor traces successful RPC calls and sets trailing metadata."""
    async def run_test():
        interceptor = ObservabilityInterceptor()

        async def dummy_behavior(request, context):
            return {"status": "ok"}

        handler = grpc.unary_unary_rpc_method_handler(dummy_behavior)
        continuation = AsyncMock(return_value=handler)

        call_details = MagicMock()
        call_details.method = "/chirp.PostsService/GetPost"
        call_details.invocation_metadata = (("x-trace-id", "trace-client-sent-999"),)

        result_handler = await interceptor.intercept_service(continuation, call_details)
        assert result_handler is not None
        assert result_handler.unary_unary is not None

        mock_context = AsyncMock()
        mock_context.set_trailing_metadata = MagicMock()
        response = await result_handler.unary_unary({}, mock_context)

        assert response == {"status": "ok"}
        mock_context.set_trailing_metadata.assert_called_once()
        trailing = mock_context.set_trailing_metadata.call_args[0][0]
        assert ("x-trace-id", "trace-client-sent-999") in trailing

    asyncio.run(run_test())


def test_observability_interceptor_error_abort():
    """Verify ObservabilityInterceptor catches domain errors and aborts with proper gRPC status."""
    async def run_test():
        interceptor = ObservabilityInterceptor()

        async def failing_behavior(request, context):
            raise NotFoundError("Resource missing")

        handler = grpc.unary_unary_rpc_method_handler(failing_behavior)
        continuation = AsyncMock(return_value=handler)

        call_details = MagicMock()
        call_details.method = "/chirp.PostsService/GetPost"
        call_details.invocation_metadata = ()

        result_handler = await interceptor.intercept_service(continuation, call_details)
        assert result_handler is not None
        assert result_handler.unary_unary is not None

        mock_context = AsyncMock()
        mock_context.set_trailing_metadata = MagicMock()
        await result_handler.unary_unary({}, mock_context)
        mock_context.abort.assert_called_once_with(grpc.StatusCode.NOT_FOUND, "Resource missing")

    asyncio.run(run_test())
