from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from ..logging_config import logger


async def error_handler_middleware(request: Request, call_next):
    """Global error handling middleware."""
    try:
        return await call_next(request)
    except IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Database constraint violated"},
        )
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
