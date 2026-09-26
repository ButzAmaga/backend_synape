"""
Purpose: Generates and attaches unique correlation request IDs to incoming HTTP requests.
Flow:
      1. Read inbound X-Request-ID header if supplied by client.
      2. Generate fallback unique ID string prefixed with req_ if header is missing.
      3. Attach request_id to request.state and outbound HTTP response headers.
Inputs: Inbound Starlette Request object.
Outputs: Passes request downstream and attaches X-Request-ID header to Response.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Purpose: Middleware component for HTTP request tracking and tracing.
    Flow:
          1. Extract or generate unique request correlation identifier.
          2. Store correlation ID on request state object.
          3. Call downstream request handlers.
          4. Inject correlation ID into outbound HTTP response header.
    Inputs: Inbound HTTP Request.
    Outputs: Processed HTTP Response with trace metadata headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Purpose: Intercepts HTTP requests to inject and propagate correlation IDs.
        Flow:
              1. Check inbound headers for existing X-Request-ID.
              2. Generate a new UUID-backed correlation ID if missing.
              3. Persist ID in request.state.request_id.
              4. Await downstream request execution.
              5. Append X-Request-ID header to outbound HTTP response.
        Inputs: Inbound Request object and downstream call_next callable.
        Outputs: Outbound Response object containing X-Request-ID header.
        """
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response