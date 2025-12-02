from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import create_all_tables
from src.api.auth import router as auth_router
from src.api.users import router as users_router

openapi_tags = [
    {"name": "Health", "description": "Health and diagnostics"},
    {"name": "Auth", "description": "Authentication and authorization"},
    {"name": "Users", "description": "User management"},
    {"name": "Saved Recipes", "description": "Save and manage favorite recipes"},
]

app = FastAPI(
    title="Recipe Explorer API",
    description="Backend for the Recipe Explorer app. Provides endpoints for recipes, users, authentication, and saved recipes.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: read from env CORS_ALLOWED_ORIGINS in a later step
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database tables if they do not exist."""
    # Create tables for SQLite persistence
    create_all_tables()


@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Simple health check endpoint.

    Returns:
        JSON object with health message.
    """
    return {"message": "Healthy"}


# Include routers
app.include_router(auth_router)
app.include_router(users_router)
