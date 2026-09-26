"""
Purpose: Defines standardized Pydantic error response schemas for predictable API errors.
Flow:
      1. Structure individual error details with error code, message, and correlation ID.
      2. Wrap detail payload inside top-level error response model.
Inputs: Raw error details passed from exception handlers or controllers.
Outputs: Validated and serialized Pydantic JSON schema models.
"""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Purpose: Represents granular error metadata attributes.
    Flow:
          1. Define code, message, and requestId fields.
    Inputs: String attributes for error classification and tracing.
    Outputs: Serialized error detail object.
    """

    code: str = Field(..., example="INTERNAL_SERVER_ERROR")
    message: str = Field(..., example="An unexpected server error occurred.")
    requestId: str = Field(..., example="req_abc123xyz")


class ErrorResponse(BaseModel):
    """
    Purpose: Encapsulates standard API error responses.
    Flow:
          1. Nest ErrorDetail schema under top-level error key.
    Inputs: Populated ErrorDetail instance.
    Outputs: Standardized error JSON model.
    """

    error: ErrorDetail