"""
Purpose: Intercepts unhandled application exceptions and converts them into standardized error responses.
Flow:
      1. Catch unhandled exceptions raised during HTTP request lifecycle.
      2. Extract request correlation ID from request state.
      3. Log exception details with request correlation context to error logger.
      4. Format sanitized error payload stripping sensitive stack trace details.
Inputs: Inbound Request object and caught Exception object.
Outputs: JSONResponse containing standardized ErrorResponse schema and HTTP status 500.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.schemas.error import ErrorResponse, ErrorDetail

logger = logging.getLogger("api.errors")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Purpose: Converts internal unhandled server errors into sanitized HTTP 500 responses.
    Flow:
          1. Retrieve correlation ID from request.state.
          2. Write structured error log entry with stack trace details.
          3. Construct generic ErrorResponse instance.
          4. Return JSONResponse with HTTP 500 status code.
    Inputs: Request object triggering the error and the caught Exception instance.
    Outputs: JSONResponse formatted with sanitized error information.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Exception [reqId={request_id}]: {str(exc)}", exc_info=True)

    error_payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please try again.",
            requestId=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )