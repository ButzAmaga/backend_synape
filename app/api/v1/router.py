"""
Purpose: Aggregates and routes all API v1 endpoint modules under unified router prefix.
Flow:
      1. Instantiate central APIRouter instance for v1.
      2. Register sub-routers for health check and future feature endpoints.
Inputs: APIRouter endpoints from v1 endpoint modules.
Outputs: Exposes unified v1 router instance to main FastAPI application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import sessions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])