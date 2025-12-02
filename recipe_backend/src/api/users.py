from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import schemas, models
from src.api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/me",
    summary="Get current authenticated user",
    response_model=schemas.UserPublic,
    responses={401: {"description": "Unauthorized"}},
)
def read_users_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.UserPublic:
    """Return the profile of the current authenticated user."""
    return current_user
