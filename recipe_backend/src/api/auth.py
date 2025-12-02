from datetime import datetime, timedelta
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from src.db import schemas, models
from src.db.crud import get_user_by_email
from src.db.database import get_db

# Load env for secrets
load_dotenv()

# Settings from environment
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if not JWT_SECRET:
    # It's okay to run locally without setting this, but raise a clear error on use.
    # The first token creation/verification will raise if secret is missing.
    pass

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme setup - clients will use "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["Auth"])

# Pydantic schema for signup body
class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Plain text password")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored hash."""
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate user with email and password; returns user if valid else None."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _ensure_secret():
    """Raise a clear error if JWT secret is not configured."""
    if not JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. Please configure it in the .env file."
        )


# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to include in the token (will be copied).
        expires_delta: Optional timedelta for expiration; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    _ensure_secret()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# PUBLIC_INTERFACE
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency that retrieves the current user from the provided JWT token.

    Raises:
        HTTPException 401 if token invalid/expired or user not found.
    """
    _ensure_secret()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub: str = payload.get("sub")  # we store email in 'sub'
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, sub)
    if user is None:
        raise credentials_exception
    return user


@router.post(
    "/signup",
    summary="Create a new user account",
    response_model=schemas.UserPublic,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created"},
        400: {"description": "User already exists or validation error"},
    },
)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> schemas.UserPublic:
    """Register a new user.

    Body:
        email: User email
        password: Password (min 6 chars)

    Returns:
        UserPublic model without sensitive fields.
    """
    # Reuse CRUD but ensure secure hashing before persist.
    # Override the password hashing in CRUD by building user and setting hashed password here.
    existing = get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_in = schemas.UserCreate(email=body.email, password=body.password)
    # Create using our secure hash path
    hashed = get_password_hash(user_in.password)

    user = models.User(email=user_in.email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    summary="Login and obtain access token",
    response_model=schemas.Token,
    responses={
        200: {"description": "Access token issued"},
        401: {"description": "Invalid credentials"},
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> schemas.Token:
    """Authenticate user and return a JWT access token.

    Form fields (application/x-www-form-urlencoded):
        username: Email address
        password: Password

    Returns:
        Token {access_token, token_type='bearer'}
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return schemas.Token(access_token=token, token_type="bearer")
