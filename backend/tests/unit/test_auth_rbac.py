"""Comprehensive Unit Tests for Authentication & RBAC Engine (Module 22)."""

import uuid
from datetime import timedelta

import pytest
from app.core.security import (
    create_jwt_token,
    hash_password,
    verify_jwt_token,
    verify_password,
)
from app.db.session import AsyncSessionLocal
from app.main import app
from app.schemas.auth import UserCreate
from app.services.auth_service import auth_service
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """Test cryptographic PBKDF2 password hashing and constant-time verification."""
    password = "GujaratPolice@2026"
    hashed = hash_password(password)

    assert hashed.startswith("$pbkdf2-sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


@pytest.mark.asyncio
async def test_jwt_creation_and_tamper_proofing():
    """Test JWT creation, claim decoding, expiry, and signature validation."""
    user_id = str(uuid.uuid4())
    token = create_jwt_token(
        subject=user_id,
        username="officer_sharma",
        role="INVESTIGATOR",
        token_type="access",
    )

    # 1. Valid Token Verification
    claims = verify_jwt_token(token, expected_type="access")
    assert claims["sub"] == user_id
    assert claims["username"] == "officer_sharma"
    assert claims["role"] == "INVESTIGATOR"

    # 2. Tampered Token Signature Rejection
    header, payload, sig = token.split(".")
    tampered_token = f"{header}.{payload}.INVALID_SIGNATURE"
    with pytest.raises(ValueError, match="Invalid cryptographic token signature"):
        verify_jwt_token(tampered_token, expected_type="access")

    # 3. Expired Token Rejection
    expired_token = create_jwt_token(
        subject=user_id,
        username="officer_sharma",
        role="INVESTIGATOR",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(ValueError, match="Token has expired"):
        verify_jwt_token(expired_token, expected_type="access")


@pytest.mark.asyncio
async def test_user_lifecycle_and_authentication():
    """Test user registration, role assignment, and authentication flow."""
    uid = uuid.uuid4().hex[:8]
    username = f"cop_{uid}"
    email = f"cop_{uid}@gujarat.police.gov.in"
    password = "SecurePassword@123"

    async with AsyncSessionLocal() as session:
        # Initialize default roles
        await auth_service.initialize_default_roles(session)

        # Create user
        create_payload = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name="Constable Ajay Verma",
            badge_number=f"GJ-COP-{uid}",
            role_name="OPERATOR",
        )
        user = await auth_service.create_user(session, create_payload)
        assert user.id is not None
        assert user.username == username

        # 1. Authenticate with valid credentials
        auth_user = await auth_service.authenticate(session, username, password)
        assert auth_user is not None
        assert auth_user.id == user.id
        assert auth_user.role.name == "OPERATOR"

        # 2. Authenticate with invalid password
        bad_auth = await auth_service.authenticate(session, username, "InvalidPassword")
        assert bad_auth is None

        # 3. Token Pair Generation
        token_pair = auth_service.create_token_pair(auth_user)
        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        assert "alerts:ack" in token_pair.user.permissions

        # 4. Refresh Token Flow
        refreshed = await auth_service.refresh_tokens(session, token_pair.refresh_token)
        assert refreshed.access_token is not None


@pytest.mark.asyncio
async def test_auth_rest_api_endpoints():
    """Test full REST API integration for Auth and RBAC endpoints."""
    uid = uuid.uuid4().hex[:8]
    admin_username = f"admin_{uid}"
    admin_email = f"admin_{uid}@police.gov.in"
    admin_pass = "AdminPass@2026"

    # Seed an admin user directly
    async with AsyncSessionLocal() as session:
        await auth_service.initialize_default_roles(session)
        await auth_service.create_user(
            session,
            UserCreate(
                username=admin_username,
                email=admin_email,
                password=admin_pass,
                full_name="Superintendent K. Jadeja",
                role_name="ADMIN",
                is_superuser=True,
            ),
        )


    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login Endpoint
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": admin_username, "password": admin_pass},
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()["data"]
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Me Profile Endpoint
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["username"] == admin_username
        assert "users:manage" in me_resp.json()["data"]["permissions"]

        # 3. Refresh Token Endpoint
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()["data"]

        # 4. List Roles Endpoint
        roles_resp = await client.get("/api/v1/auth/roles")
        assert roles_resp.status_code == 200
        assert roles_resp.json()["data"]["total"] >= 5

        # 5. Create New User via Admin API
        new_cop_uname = f"patrol_{uid}"
        create_user_resp = await client.post(
            "/api/v1/auth/users",
            json={
                "username": new_cop_uname,
                "email": f"{new_cop_uname}@police.gov.in",
                "password": "PatrolPassword@123",
                "full_name=" : "Officer B. Rao",
                "full_name": "Officer B. Rao",
                "role_name": "VIEWER",
            },
            headers=headers,
        )
        assert create_user_resp.status_code == 201
        new_cop_id = create_user_resp.json()["data"]["id"]

        # 6. List Users Endpoint
        users_resp = await client.get("/api/v1/auth/users", headers=headers)
        assert users_resp.status_code == 200
        assert users_resp.json()["data"]["total"] >= 2

        # 7. Update User Role
        update_resp = await client.put(
            f"/api/v1/auth/users/{new_cop_id}",
            json={"role_name": "ANALYST"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["role"] == "ANALYST"

        # 8. Telemetry Endpoint
        telem_resp = await client.get("/api/v1/auth/telemetry")
        assert telem_resp.status_code == 200
        assert telem_resp.json()["data"]["total_users"] >= 2
