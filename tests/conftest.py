"""Pytest fixtures for integration tests."""

from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, UserContext
from src.auth.models import UserProfile
from src.database import get_db
from src.main import app

_security = HTTPBearer()


@pytest.fixture
def app_with_auth_override():
    """App with get_current_user overridden to use test tokens (Bearer admin / Bearer user)."""

    async def _mock_get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ):
        token = getattr(credentials, "credentials", None) or ""
        role = "admin" if token == "admin" else "user"
        profile = UserProfile(id=uuid4(), clerk_user_id="test-user", is_active=True)
        return UserContext(profile=profile, role=role)

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield app
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def client(app_with_auth_override):
    """Async HTTP client for the FastAPI app (with auth override)."""
    transport = ASGITransport(app=app_with_auth_override)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Headers for non-admin user (used by brands dashboard tests)."""
    return {"Authorization": "Bearer user"}


@pytest.fixture
def admin_headers():
    """Headers for admin user (admin dashboard 200)."""
    return {"Authorization": "Bearer admin"}


@pytest.fixture
def non_admin_headers():
    """Headers for non-admin user (admin dashboard 403)."""
    return {"Authorization": "Bearer user"}
