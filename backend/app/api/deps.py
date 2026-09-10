"""FastAPI Security and Dependency Injection Helpers for SentinelX."""

from typing import Callable, Optional

from app.core.security import verify_jwt_token
from app.db.session import get_db
from app.models.user import Role, User
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Standard HTTP Bearer scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and authenticate current user from Bearer JWT token."""
    if not credentials or not credentials.credentials:
        # Check if running in dev without explicit token or fallback to demo admin
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Provide 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = verify_jwt_token(token, expected_type="access")
        user_id = payload.get("sub")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory ensuring authenticated user belongs to at least one of the specified roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        user_role_name = current_user.role.name if current_user.role else "VIEWER"
        if user_role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}. Current role: '{user_role_name}'.",
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: str) -> Callable:
    """Dependency factory ensuring user has all requested granular permissions."""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        user_perms = {p.name for p in current_user.role.permissions} if (current_user.role and current_user.role.permissions) else set()
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing required permissions: {missing}",
            )
        return current_user

    return permission_checker
