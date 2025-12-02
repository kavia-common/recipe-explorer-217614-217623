from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# -------------------------
# User Schemas
# -------------------------

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's email address")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Plain text password to be hashed")


class UserPublic(UserBase):
    id: int = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="User creation timestamp")

    class Config:
        from_attributes = True


# -------------------------
# Auth / Token Schemas
# -------------------------

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Type of the token")


# -------------------------
# Saved Recipe Schemas
# -------------------------

class SavedRecipeBase(BaseModel):
    recipe_id: int = Field(..., description="Spoonacular recipe ID")
    title: str = Field(..., description="Recipe title")
    image: Optional[str] = Field(None, description="Image URL")
    source_url: Optional[str] = Field(None, description="Source URL")
    aggregate_likes: Optional[int] = Field(None, description="Total likes")
    ready_in_minutes: Optional[int] = Field(None, description="Ready in minutes")
    summary: Optional[str] = Field(None, description="Short description/summary")


class SavedRecipeCreate(SavedRecipeBase):
    pass


class SavedRecipePublic(SavedRecipeBase):
    id: int = Field(..., description="Saved item ID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="When the recipe was saved")

    class Config:
        from_attributes = True
