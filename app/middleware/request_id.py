import uuid
from fastapi import Request
from ..logging_config import logger


async def request_id_middleware(request: Request, call_next):
    """Add unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={"request_id": request_id},
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        f"Request completed: {response.status_code}",
        extra={"request_id": request_id},
    )

    return response
