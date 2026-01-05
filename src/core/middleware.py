"""Application middleware."""

import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and logs."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request ID to logger context
        logger = logging.getLogger()
        old_factory = logger.makeRecord

        def make_record_with_request_id(
            name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None
        ):
            rv = old_factory(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
            rv.request_id = request_id
            return rv

        logger.makeRecord = make_record_with_request_id  # type: ignore[method-assign]

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            logger.makeRecord = old_factory  # type: ignore[method-assign]
