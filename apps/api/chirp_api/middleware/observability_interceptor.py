"""Observability and Tracing Interceptor for gRPC async server.

Extracts or generates unique trace IDs, attaches them to request context and trailing metadata,
logs structured access metrics with latency, and maps unhandled domain exceptions to gRPC status
codes.
"""

import inspect
import time

import grpc

from chirp_api.errors import map_error_to_status_code
from chirp_api.observability import (
    generate_trace_id,
    logger,
    reset_trace_id,
    set_trace_id,
)


class ObservabilityInterceptor(grpc.aio.ServerInterceptor):
    """gRPC async server interceptor for request tracing, structured logging, and error mapping."""

    async def intercept_service(self, continuation, handler_call_details):
        # Extract incoming trace ID from invocation metadata if provided
        metadata = dict(handler_call_details.invocation_metadata or ())
        trace_id = (
            metadata.get("x-trace-id")
            or metadata.get("trace-id")
            or metadata.get("x-request-id")
            or generate_trace_id()
        )

        method = handler_call_details.method

        # Proceed with continuation to get inner RPC handler
        handler = await continuation(handler_call_details)
        if not handler:
            return handler

        if handler.unary_unary:
            original_behavior = handler.unary_unary

            async def traced_unary_unary(request, context):
                token = set_trace_id(trace_id)
                start_time = time.time()

                # Attach trace ID to trailing metadata for the client response
                if hasattr(context, "set_trailing_metadata"):
                    try:
                        res = context.set_trailing_metadata(
                            (
                                ("x-trace-id", trace_id),
                                ("trace-id", trace_id),
                            )
                        )
                        if inspect.isawaitable(res):
                            await res
                    except Exception:
                        pass

                logger.info(
                    f"RPC Started: {method}",
                    extra={
                        "method": method,
                        "trace_id": trace_id,
                        "event": "rpc_start",
                    },
                )

                try:
                    if inspect.iscoroutinefunction(original_behavior):
                        response = await original_behavior(request, context)
                    else:
                        res = original_behavior(request, context)
                        if inspect.isawaitable(res):
                            response = await res
                        else:
                            response = res

                    duration_ms = round((time.time() - start_time) * 1000, 2)
                    logger.info(
                        f"RPC Completed: {method}",
                        extra={
                            "method": method,
                            "trace_id": trace_id,
                            "duration_ms": duration_ms,
                            "status": "OK",
                            "event": "rpc_complete",
                        },
                    )
                    return response

                except Exception as error:
                    duration_ms = round((time.time() - start_time) * 1000, 2)
                    status_code, error_message = map_error_to_status_code(error)

                    logger.error(
                        f"RPC Failed: {method} - {error_message}",
                        extra={
                            "method": method,
                            "trace_id": trace_id,
                            "duration_ms": duration_ms,
                            "status": status_code.name,
                            "error": str(error),
                            "event": "rpc_error",
                        },
                        exc_info=True,
                    )

                    await context.abort(status_code, error_message)

                finally:
                    reset_trace_id(token)

            return grpc.unary_unary_rpc_method_handler(
                traced_unary_unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        return handler
