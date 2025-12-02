import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import create_all_tables
from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.api.recipes import router as recipes_router

# Define OpenAPI tags for grouping endpoints
openapi_tags = [
    {"name": "Health", "description": "Health and diagnostics"},
    {"name": "Auth", "description": "Authentication and authorization"},
    {"name": "Users", "description": "User management"},
    {"name": "Saved Recipes", "description": "Save and manage favorite recipes"},
    {"name": "Recipes", "description": "Recipe search and details from Spoonacular"},
]

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Recipe Explorer API",
    description="Backend for the Recipe Explorer app. Provides endpoints for recipes, users, authentication, and saved recipes.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# Configure CORS using environment variable CORS_ALLOWED_ORIGINS
# Comma-separated origins, e.g. "http://localhost:3000,https://example.com"
# Defaults to "http://localhost:3000" for local development to work with the React frontend.
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
allow_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

# CORSMiddleware handles OPTIONS preflight automatically for allowed origins/methods/headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Initialize database tables if they do not exist.

    Ensures SQLAlchemy models are created at application startup so the app
    is ready without manual migration steps for initial schema.
    """
    create_all_tables()

# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Root", description="Public root endpoint to verify the API is up.")
def root():
    """Public root endpoint for quick connectivity checks.

    Returns:
        dict: {"status": "ok", "service": "Recipe Explorer API"}
    """
    return {"status": "ok", "service": "Recipe Explorer API"}

# PUBLIC_INTERFACE
@app.get(
    "/health",
    tags=["Health"],
    summary="Health",
    description="Simple health check endpoint used by frontend and monitors.",
    responses={200: {"description": "Service is healthy"}},
)
def health():
    """Health check endpoint.

    Returns:
        dict: {"status": "ok"}
    """
    return {"status": "ok"}

# Include routers for all API modules
# These imports are already resolved above; ensure they are included here.
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(recipes_router)
