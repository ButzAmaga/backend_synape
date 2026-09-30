"""
Purpose: Initializes FastAPI application gateway, registers middleware, and defines startup lifecycle hooks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.pipeline import reset_stale_processing_tasks
from app.api.middleware.correlation import CorrelationIdMiddleware
from app.api.middleware.error_handler import global_exception_handler
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Purpose: Manages application startup and shutdown lifecycle events.
    Flow:
          1. Invoke database initialization to set SQLite WAL mode and create tables.
          2. Execute startup crash-recovery routine to mark stale processing tasks as FAILED.
          3. Yield control to running FastAPI application context.
          4. Perform clean shutdown operations upon application termination.
    """
    await init_db()
    await reset_stale_processing_tasks()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)

# Include API v1 Router
app.include_router(api_router)