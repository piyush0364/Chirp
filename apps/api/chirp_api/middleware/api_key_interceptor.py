"""API Key Interceptor for gRPC server."""

import os

import grpc

API_KEY = os.environ.get("INTERNAL_API_KEY", "chirp-internal-api-key-dev")

class APIKeyInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that validates the x-api-key metadata on every request."""

    async def intercept_service(self, continuation, handler_call_details):
        # Extract the x-api-key from the invocation metadata
        metadata = dict(handler_call_details.invocation_metadata)
        client_api_key = metadata.get("x-api-key")

        # In a real production system, this could check against a list of valid keys
        # or be skipped for certain health check endpoints if needed.
        if client_api_key != API_KEY:
            # Return an UNAUTHENTICATED error if the API key is missing or invalid
            async def abort(request, context):
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing API key")

            return grpc.unary_unary_rpc_method_handler(abort)

        return await continuation(handler_call_details)
