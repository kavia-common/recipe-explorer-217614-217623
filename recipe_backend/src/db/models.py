from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """User account record."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to saved recipes
    saved_recipes = relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")


class SavedRecipe(Base):
    """Saved recipe by a user, unique per (user_id, recipe_id)."""
    __tablename__ = "saved_recipes"
    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic recipe info saved from Spoonacular
    recipe_id = Column(Integer, nullable=False, index=True)  # Spoonacular recipe ID
    title = Column(String(500), nullable=False)
    image = Column(String(1000), nullable=True)
    source_url = Column(String(1000), nullable=True)
    aggregate_likes = Column(Integer, nullable=True)
    ready_in_minutes = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="saved_recipes")
