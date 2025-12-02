from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import schemas, models
from src.api.auth import get_current_user
from src.db import crud

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


@router.get(
    "/me/saved",
    summary="List saved recipes for current user",
    description="Returns all recipes saved by the authenticated user.",
    response_model=List[schemas.SavedRecipePublic],
    responses={
        200: {"description": "List of saved recipes"},
        401: {"description": "Unauthorized"},
    },
)
def list_my_saved_recipes(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[schemas.SavedRecipePublic]:
    """List saved recipes for the current user."""
    return crud.list_saved(db, user_id=current_user.id)


@router.post(
    "/me/saved",
    summary="Save or update a recipe for current user",
    description="Create a saved recipe for the authenticated user, or update it if it already exists for the given recipe_id.",
    response_model=schemas.SavedRecipePublic,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Saved (created or updated)"},
        400: {"description": "Validation or integrity error"},
        401: {"description": "Unauthorized"},
    },
)
def save_recipe_for_me(
    body: schemas.SavedRecipeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.SavedRecipePublic:
    """Save or update a recipe for the current user. Uniqueness is enforced on (user_id, recipe_id)."""
    try:
        saved = crud.upsert_saved(db, user_id=current_user.id, data=body)
        return saved
    except Exception as e:
        # Provide a user-friendly error; details can be logged in a real-world app
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete(
    "/me/saved/{recipe_id}",
    summary="Delete a saved recipe by recipe_id",
    description="Deletes the saved recipe for the current user by its Spoonacular recipe_id.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Deleted"},
        401: {"description": "Unauthorized"},
        404: {"description": "Saved recipe not found"},
    },
)
def delete_saved_recipe_for_me(
    recipe_id: int = Path(..., description="Spoonacular recipe ID"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a saved recipe for the current user by its Spoonacular recipe ID."""
    deleted = crud.remove_saved(db, user_id=current_user.id, recipe_id=recipe_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved recipe not found")
    # 204 No Content
    return None
