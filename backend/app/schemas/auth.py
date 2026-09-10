"""Authentication, RBAC, and Token Management Schemas for SentinelX."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    """User login credential payload."""
    username: str = Field(..., description="Badge ID, username, or registered email")
    password: str = Field(..., description="Plaintext secret password")


class UserProfileResponse(BaseModel):
    """Public user identity and permissions profile."""
    id: str
    username: str
    email: str
    full_name: str
    badge_number: Optional[str] = None
    department: str
    role: str
    is_active: bool
    is_superuser: bool
    permissions: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Bearer token pair and user profile payload."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    refresh_token: str
    user: UserProfileResponse


class RefreshTokenRequest(BaseModel):
    """Token refresh payload."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password update request."""
    old_password: str
    new_password: str = Field(..., min_length=8, description="New strong password (min 8 chars)")


class UserCreate(BaseModel):
    """Schema for registering a new police personnel user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User official email address")
    password: str = Field(..., min_length=8)
    full_name: str
    badge_number: Optional[str] = None
    department: str = Field(default="Gujarat Police")
    role_name: str = Field(default="OPERATOR", description="ADMIN, OPERATOR, INVESTIGATOR, ANALYST, VIEWER")
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Schema for modifying user metadata and permissions."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    badge_number: Optional[str] = None
    department: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None



class UserListResponse(BaseModel):
    """Paginated user listing response."""
    total: int
    items: List[UserProfileResponse]


class PermissionResponse(BaseModel):
    """Granular permission descriptor."""
    id: str
    name: str
    description: Optional[str] = None
    category: str


class RoleResponse(BaseModel):
    """System RBAC Role with assigned permissions."""
    id: str
    name: str
    description: Optional[str] = None
    is_system_default: bool
    permissions: List[str]


class RoleListResponse(BaseModel):
    """Collection of RBAC roles."""
    total: int
    items: List[RoleResponse]


class AuthTelemetry(BaseModel):
    """Authentication and access telemetry."""
    total_users: int
    active_users: int
    total_logins_24h: int
    failed_logins_24h: int
    roles_distribution: Dict[str, int]
