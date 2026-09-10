"""Authentication, RBAC Engine, and User Lifecycle Service for SentinelX."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    create_jwt_token,
    hash_password,
    verify_jwt_token,
    verify_password,
)
from app.models.user import Permission, Role, RoleType, User
from app.schemas.auth import (
    AuthTelemetry,
    RoleResponse,
    TokenResponse,
    UserCreate,
    UserProfileResponse,
    UserUpdate,
)

# Standard permissions definition
DEFAULT_PERMISSIONS: Dict[str, Tuple[str, str]] = {
    "cameras:read": ("View CCTV camera registry and live streams", "cameras"),
    "cameras:write": ("Register, update, and manage CCTV cameras", "cameras"),
    "vehicles:search": ("Execute sub-200ms spatial-temporal vehicle queries", "intelligence"),
    "watchlist:read": ("View vehicle hotlists and watchlists", "watchlist"),
    "watchlist:write": ("Create and update vehicle watchlists", "watchlist"),
    "alerts:read": ("Receive and view real-time hotlist alerts", "alerts"),
    "alerts:ack": ("Acknowledge, triage, and resolve alerts", "alerts"),
    "evidence:read": ("View forensic evidence vault snapshots", "evidence"),
    "evidence:export": ("Export Section 65B certified evidence dossiers", "evidence"),
    "audit:read": ("Inspect immutable system audit trails", "audit"),
    "users:manage": ("Manage user accounts, roles, and access credentials", "admin"),
    "system:manage": ("Configure AI pipelines, buffers, and system settings", "system"),
}

DEFAULT_ROLE_PERMISSIONS: Dict[RoleType, List[str]] = {
    RoleType.ADMIN: list(DEFAULT_PERMISSIONS.keys()),
    RoleType.OPERATOR: [
        "cameras:read",
        "vehicles:search",
        "watchlist:read",
        "alerts:read",
        "alerts:ack",
        "evidence:read",
    ],
    RoleType.INVESTIGATOR: [
        "cameras:read",
        "vehicles:search",
        "watchlist:read",
        "watchlist:write",
        "alerts:read",
        "alerts:ack",
        "evidence:read",
        "evidence:export",
        "audit:read",
    ],
    RoleType.ANALYST: [
        "cameras:read",
        "vehicles:search",
        "watchlist:read",
        "alerts:read",
        "evidence:read",
        "audit:read",
    ],
    RoleType.VIEWER: [
        "cameras:read",
        "vehicles:search",
        "alerts:read",
        "evidence:read",
    ],
}


class AuthService:
    """Authentication and RBAC Security Management Service."""

    def __init__(self) -> None:
        self._login_attempts_24h: int = 0
        self._failed_logins_24h: int = 0

    async def initialize_default_roles(self, db: AsyncSession) -> None:
        """Guarantee all 5 standard roles and granular permissions exist in database."""
        # 1. Create permissions
        existing_perms_res = await db.execute(select(Permission))
        existing_perms = {p.name: p for p in existing_perms_res.scalars().all()}

        for perm_name, (desc, cat) in DEFAULT_PERMISSIONS.items():
            if perm_name not in existing_perms:
                perm_obj = Permission(
                    id=str(uuid.uuid4()),
                    name=perm_name,
                    description=desc,
                    category=cat,
                )
                db.add(perm_obj)
                existing_perms[perm_name] = perm_obj

        await db.flush()

        # 2. Create roles and link permissions
        for role_type, allowed_perms in DEFAULT_ROLE_PERMISSIONS.items():
            role_res = await db.execute(
                select(Role).options(selectinload(Role.permissions)).where(Role.name == role_type.value)
            )
            role = role_res.scalar_one_or_none()
            target_perms = [existing_perms[p] for p in allowed_perms if p in existing_perms]

            if not role:
                role = Role(
                    id=str(uuid.uuid4()),
                    name=role_type.value,
                    description=f"{role_type.value.capitalize()} role with designated operational permissions.",
                    is_system_default=True,
                    permissions=target_perms,
                )
                db.add(role)
            else:
                role.permissions = target_perms

        await db.commit()
        logger.info("Initialized default SentinelX RBAC roles and permissions.")


    async def authenticate(
        self,
        db: AsyncSession,
        username_or_email: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate user credentials with timing-safe verification."""
        self._login_attempts_24h += 1
        query = select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            self._failed_logins_24h += 1
            return None

        if not verify_password(password, user.hashed_password):
            self._failed_logins_24h += 1
            return None

        return user

    def get_user_permissions(self, user: User) -> List[str]:
        """Extract flat permission string list from user role."""
        if user.is_superuser:
            return list(DEFAULT_PERMISSIONS.keys())
        if user.role and user.role.permissions:
            return [p.name for p in user.role.permissions]
        return []

    def get_user_profile(self, user: User) -> UserProfileResponse:
        """Convert ORM User to public identity profile."""
        role_name = user.role.name if user.role else ("ADMIN" if user.is_superuser else "VIEWER")
        permissions = self.get_user_permissions(user)

        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            badge_number=user.badge_number,
            department=user.department,
            role=role_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            permissions=permissions,
            created_at=user.created_at,
        )

    def create_token_pair(self, user: User) -> TokenResponse:
        """Generate JWT access & refresh token pair."""
        role_name = user.role.name if user.role else ("ADMIN" if user.is_superuser else "VIEWER")
        profile = self.get_user_profile(user)

        access_token = create_jwt_token(
            subject=user.id,
            username=user.username,
            role=role_name,
            token_type="access",
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_jwt_token(
            subject=user.id,
            username=user.username,
            role=role_name,
            token_type="refresh",
            expires_delta=timedelta(days=7),
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
            user=profile,
        )

    async def refresh_tokens(self, db: AsyncSession, refresh_token_str: str) -> TokenResponse:
        """Issue new token pair from verified refresh token."""
        payload = verify_jwt_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")

        query = select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise ValueError("User account is inactive or not found.")

        return self.create_token_pair(user)

    async def create_user(self, db: AsyncSession, payload: UserCreate) -> User:
        """Register a new police personnel user."""
        # Check uniqueness
        existing = await db.execute(
            select(User).where((User.username == payload.username) | (User.email == payload.email))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"User with username '{payload.username}' or email '{payload.email}' already exists.")

        # Resolve role
        role_res = await db.execute(select(Role).where(Role.name == payload.role_name))
        role = role_res.scalar_one_or_none()
        role_id = role.id if role else None

        user = User(
            id=str(uuid.uuid4()),
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            badge_number=payload.badge_number,
            department=payload.department,
            hashed_password=hash_password(payload.password),
            role_id=role_id,
            is_active=True,
            is_superuser=payload.is_superuser,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(self, db: AsyncSession, user_id: str, payload: UserUpdate) -> User:
        """Update existing user properties or role."""
        query = select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found.")

        if payload.email is not None:
            user.email = payload.email
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.badge_number is not None:
            user.badge_number = payload.badge_number
        if payload.department is not None:
            user.department = payload.department
        if payload.is_active is not None:
            user.is_active = payload.is_active
        if payload.password is not None and payload.password.strip():
            user.hashed_password = hash_password(payload.password)
        if payload.role_name is not None:
            role_res = await db.execute(select(Role).where(Role.name == payload.role_name))
            role = role_res.scalar_one_or_none()
            if role:
                user.role_id = role.id

        await db.commit()
        await db.refresh(user)
        return user

    async def change_password(self, db: AsyncSession, user: User, old_pass: str, new_pass: str) -> bool:
        """Change user password with old password verification."""
        if not verify_password(old_pass, user.hashed_password):
            raise ValueError("Current password verification failed.")

        user.hashed_password = hash_password(new_pass)
        await db.commit()
        return True

    async def list_users(
        self,
        db: AsyncSession,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[User], int]:
        """Query users with role filters and pagination."""
        query = select(User).options(selectinload(User.role).selectinload(Role.permissions))
        count_q = select(func.count(User.id))

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_q = count_q.where(User.is_active == is_active)
        if role_name:
            query = query.join(User.role).where(Role.name == role_name)
            count_q = count_q.join(User.role).where(Role.name == role_name)

        total_res = await db.execute(count_q)
        total_count = total_res.scalar() or 0

        query = query.order_by(User.username.asc()).offset(offset).limit(limit)
        res = await db.execute(query)
        users = res.scalars().all()

        return users, total_count

    async def list_roles(self, db: AsyncSession) -> List[RoleResponse]:
        """List all system roles and their granted permissions."""
        query = select(Role).options(selectinload(Role.permissions)).order_by(Role.name.asc())
        res = await db.execute(query)
        roles = res.scalars().all()

        return [
            RoleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                is_system_default=r.is_system_default,
                permissions=[p.name for p in r.permissions] if r.permissions else [],
            )
            for r in roles
        ]

    async def get_telemetry(self, db: AsyncSession) -> AuthTelemetry:
        """Retrieve live authentication telemetry and user role distribution."""
        total_res = await db.execute(select(func.count(User.id)))
        total_users = total_res.scalar() or 0

        active_res = await db.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
        active_users = active_res.scalar() or 0

        # Distribution
        dist_res = await db.execute(
            select(Role.name, func.count(User.id)).outerjoin(User, User.role_id == Role.id).group_by(Role.name)
        )
        roles_dist = {row[0]: row[1] for row in dist_res.all() if row[0]}

        return AuthTelemetry(
            total_users=total_users,
            active_users=active_users,
            total_logins_24h=self._login_attempts_24h,
            failed_logins_24h=self._failed_logins_24h,
            roles_distribution=roles_dist,
        )


# Global singleton instance
auth_service = AuthService()
