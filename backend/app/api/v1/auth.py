"""Authentication and Role-Based Access Control (RBAC) REST API Endpoints for SentinelX."""

from typing import Optional

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthTelemetry,
    ChangePasswordRequest,
    RefreshTokenRequest,
    RoleListResponse,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserUpdate,
)
from app.schemas.common import APIResponse
from app.services.auth_service import auth_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate police personnel and obtain JWT token pair",
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Verify username/badge and password, issuing access & refresh tokens."""
    user = await auth_service.authenticate(
        db=db,
        username_or_email=payload.username,
        password=payload.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or inactive account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = auth_service.create_token_pair(user)
    return APIResponse(data=tokens, message="Authentication successful.")


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Obtain fresh access token using refresh token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Verify refresh token and issue new token pair."""
    try:
        new_tokens = await auth_service.refresh_tokens(db, payload.refresh_token)
        return APIResponse(data=new_tokens, message="Tokens refreshed successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=APIResponse[UserProfileResponse],
    summary="Get current authenticated user identity and permissions",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserProfileResponse]:
    """Retrieve logged-in user profile with active role permissions."""
    profile = auth_service.get_user_profile(current_user)
    return APIResponse(data=profile, message="User profile retrieved.")


@router.post(
    "/change-password",
    response_model=APIResponse[dict],
    summary="Update account password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Update current user password with old password verification."""
    try:
        await auth_service.change_password(
            db=db,
            user=current_user,
            old_pass=payload.old_password,
            new_pass=payload.new_password,
        )
        return APIResponse(data={"updated": True}, message="Password updated successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password update failed: {str(e)}",
        )


@router.get(
    "/users",
    response_model=APIResponse[UserListResponse],
    summary="List registered police command center users",
)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles("ADMIN", "INVESTIGATOR")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserListResponse]:
    """Query user directory with role-based authorization."""
    users, total = await auth_service.list_users(
        db=db,
        role_name=role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    items = [auth_service.get_user_profile(u) for u in users]
    return APIResponse(data=UserListResponse(total=total, items=items), message=f"Retrieved {len(items)} users.")


@router.post(
    "/users",
    response_model=APIResponse[UserProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new police officer account (Admin only)",
)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfileResponse]:
    """Create new police operator or investigator account."""
    try:
        new_user = await auth_service.create_user(db, payload)
        profile = auth_service.get_user_profile(new_user)
        return APIResponse(data=profile, message=f"User '{new_user.username}' created successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User creation failed: {str(e)}",
        )


@router.put(
    "/users/{user_id}",
    response_model=APIResponse[UserProfileResponse],
    summary="Update user details, status, or role (Admin only)",
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserProfileResponse]:
    """Modify user account settings or assign new RBAC role."""
    try:
        updated_user = await auth_service.update_user(db, user_id, payload)
        profile = auth_service.get_user_profile(updated_user)
        return APIResponse(data=profile, message="User updated successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User update failed: {str(e)}",
        )


@router.get(
    "/roles",
    response_model=APIResponse[RoleListResponse],
    summary="List system RBAC roles and permissions",
)
async def list_roles(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[RoleListResponse]:
    """Get all 5 system roles and their assigned permission matrices."""
    roles = await auth_service.list_roles(db)
    return APIResponse(data=RoleListResponse(total=len(roles), items=roles), message="Roles retrieved.")


@router.post(
    "/seed-roles",
    response_model=APIResponse[dict],
    summary="Initialize or reset default SentinelX RBAC roles",
)
async def seed_roles(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Guarantee standard roles (ADMIN, OPERATOR, INVESTIGATOR, ANALYST, VIEWER) exist."""
    await auth_service.initialize_default_roles(db)
    return APIResponse(data={"initialized": True}, message="Default roles and permissions synchronized.")


@router.get(
    "/telemetry",
    response_model=APIResponse[AuthTelemetry],
    summary="Authentication and access telemetry",
)
async def get_auth_telemetry(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuthTelemetry]:
    """Retrieve user statistics and login telemetry."""
    telemetry = await auth_service.get_telemetry(db)
    return APIResponse(data=telemetry, message="Auth telemetry retrieved.")
