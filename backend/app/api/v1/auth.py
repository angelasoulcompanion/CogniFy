"""
Authentication API Endpoints
Login, logout, register, and token management
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_tokens,
    decode_token,
    get_current_user,
    TokenPayload,
    TokenResponse,
)
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.user import User, UserRole


router = APIRouter()

# Initialize repository
user_repo = UserRepository()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User response (without password)"""
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with tokens and user info"""
    user: UserResponse
    tokens: TokenResponse


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login with username and password.
    Returns JWT access and refresh tokens.
    """
    # Find user by username
    user = await user_repo.get_by_username(request.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Update last login
    await user_repo.update_last_login(user.user_id)

    # Create tokens
    tokens = create_tokens(user.user_id, user.role.value)

    return AuthResponse(
        user=UserResponse(
            user_id=str(user.user_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        ),
        tokens=tokens
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    Returns JWT tokens for immediate login.
    """
    # Check if email already exists
    if await user_repo.email_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=UserRole.USER,
    )

    # Save to database
    user = await user_repo.create(user)

    # Create tokens
    tokens = create_tokens(user.user_id, user.role.value)

    return AuthResponse(
        user=UserResponse(
            user_id=str(user.user_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        ),
        tokens=tokens
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user to verify they still exist and are active
    user = await user_repo.get_by_id(UUID(payload.sub))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    return create_tokens(user.user_id, user.role.value)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    """
    user = await user_repo.get_by_id(UUID(current_user.sub))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        user_id=str(user.user_id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.post("/logout")
async def logout(current_user: TokenPayload = Depends(get_current_user)):
    """
    Logout current user.
    Note: JWT tokens are stateless, so this endpoint is mainly for client-side cleanup.
    For true token invalidation, implement a token blacklist.
    """
    return {"message": "Successfully logged out"}


@router.patch("/me/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Change current user's password.
    """
    # Get user
    user = await user_repo.get_by_id(UUID(current_user.sub))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify old password
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password"
        )

    # Update password
    new_hash = hash_password(new_password)
    await user_repo.update_password(user.user_id, new_hash)

    return {"message": "Password updated successfully"}
