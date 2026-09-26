"""
Purpose: Initializes FastAPI application gateway, registers middleware, and defines startup lifecycle hooks.
Flow:
      1. Execute lifespan hook initializing SQLite WAL database setup.
      2. Instantiate main FastAPI application instance.
      3. Attach CORS middleware restricting origin to local client.
      4. Attach correlation ID tracking middleware.
      5. Bind global exception handler for unhandled server errors.
Inputs: Application configuration settings and middleware components.
Outputs: Fully configured FastAPI application object ready for Uvicorn server invocation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.middleware.correlation import CorrelationIdMiddleware
from app.api.middleware.error_handler import global_exception_handler
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Purpose: Manages application startup and shutdown lifecycle events.
    Flow:
          1. Invoke database initialization to set SQLite WAL mode and create tables.
          2. Yield control to running FastAPI application context.
          3. Perform clean shutdown operations upon application termination.
    Inputs: FastAPI application instance.
    Outputs: Async context manager yielding runtime control to server lifecycle.
    """
    await init_db()
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