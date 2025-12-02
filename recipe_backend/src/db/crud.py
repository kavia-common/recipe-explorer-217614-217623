from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas

try:
    # Prefer secure hashing from the auth module if available
    from src.api.auth import get_password_hash as _secure_hash_password  # type: ignore
except Exception:
    _secure_hash_password = None  # fallback to stub below


def _hash_password_stub(plain_password: str) -> str:
    """Temporary password hash implementation (fallback only)."""
    return f"stub$sha256like${plain_password[::-1]}"


# PUBLIC_INTERFACE
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Return user by email if exists, else None."""
    stmt = select(models.User).where(models.User.email == email)
    return db.execute(stmt).scalar_one_or_none()


# PUBLIC_INTERFACE
def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    """Create a new user with hashed password."""
    if get_user_by_email(db, user_in.email) is not None:
        raise ValueError("User with this email already exists")

    password_hash = (
        _secure_hash_password(user_in.password) if _secure_hash_password else _hash_password_stub(user_in.password)
    )

    user = models.User(
        email=user_in.email,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# PUBLIC_INTERFACE
def list_saved(db: Session, user_id: int) -> List[models.SavedRecipe]:
    """List saved recipes for a user."""
    stmt = select(models.SavedRecipe).where(models.SavedRecipe.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


# PUBLIC_INTERFACE
def upsert_saved(db: Session, user_id: int, data: schemas.SavedRecipeCreate) -> models.SavedRecipe:
    """Insert or update a saved recipe for the given user and recipe_id."""
    # Try to find existing
    stmt = select(models.SavedRecipe).where(
        models.SavedRecipe.user_id == user_id,
        models.SavedRecipe.recipe_id == data.recipe_id,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        # Update fields
        existing.title = data.title
        existing.image = data.image
        existing.source_url = data.source_url
        existing.aggregate_likes = data.aggregate_likes
        existing.ready_in_minutes = data.ready_in_minutes
        existing.summary = data.summary
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    item = models.SavedRecipe(
        user_id=user_id,
        recipe_id=data.recipe_id,
        title=data.title,
        image=data.image,
        source_url=data.source_url,
        aggregate_likes=data.aggregate_likes,
        ready_in_minutes=data.ready_in_minutes,
        summary=data.summary,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # In case of race condition on unique constraint, re-select and update
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.title = data.title
            existing.image = data.image
            existing.source_url = data.source_url
            existing.aggregate_likes = data.aggregate_likes
            existing.ready_in_minutes = data.ready_in_minutes
            existing.summary = data.summary
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        raise
    db.refresh(item)
    return item


# PUBLIC_INTERFACE
def remove_saved(db: Session, user_id: int, recipe_id: int) -> bool:
    """Remove a saved recipe. Returns True if a row was deleted."""
    stmt = select(models.SavedRecipe).where(
        models.SavedRecipe.user_id == user_id,
        models.SavedRecipe.recipe_id == recipe_id,
    )
    row = db.execute(stmt).scalar_one_or_none()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
