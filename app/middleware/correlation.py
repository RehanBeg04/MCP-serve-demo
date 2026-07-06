"""ASGI middleware: correlation ID generation/propagation."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.auth.context import bind_correlation_id, reset_correlation_id

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(CORRELATION_ID_HEADER)
        correlation_id = incoming if incoming else str(uuid.uuid4())

        token = bind_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id
        try:
            response = await call_next(request)
        finally:
            reset_correlation_id(token)

        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response