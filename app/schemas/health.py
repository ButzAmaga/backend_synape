"""
Purpose: Defines Pydantic schemas for health check and readiness endpoints.
Flow:
      1. Declare response attributes for application status, database connectivity, and host disk metrics.
Inputs: Health check evaluation metrics from service layer.
Outputs: Validated health status JSON response model.
"""

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Purpose: Represents system operational health status details.
    Flow:
          1. Serialize operational state string ("HEALTHY" or "UNHEALTHY").
          2. Indicate database connectivity status flag.
          3. Report host filesystem free and total storage bytes.
    Inputs: Operational health status variables.
    Outputs: Serialized health response model.
    """

    status: str = Field(..., json_schema_extra={"example": "HEALTHY"})
    database_connected: bool = Field(..., json_schema_extra={"example": True})
    disk_free_bytes: int = Field(..., json_schema_extra={"example": 107374182400})
    disk_total_bytes: int = Field(..., json_schema_extra={"example": 512075251712})