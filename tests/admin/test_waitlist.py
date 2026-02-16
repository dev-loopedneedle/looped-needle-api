"""Integration tests for admin waitlist GET /api/v1/admin/waitlist."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_waitlist_returns_200_and_list(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/admin/waitlist with admin auth returns 200 and paginated list."""
    response = await client.get(
        "/api/v1/admin/waitlist",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert data["total"] >= 0
    assert data["limit"] >= 1
    assert data["offset"] >= 0


@pytest.mark.asyncio
async def test_admin_waitlist_non_admin_returns_403(
    client: AsyncClient, non_admin_headers: dict
):
    """GET /api/v1/admin/waitlist with non-admin auth returns 403."""
    response = await client.get(
        "/api/v1/admin/waitlist",
        headers=non_admin_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_waitlist_pagination_params(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/admin/waitlist accepts limit and offset query params."""
    response = await client.get(
        "/api/v1/admin/waitlist",
        headers=admin_headers,
        params={"limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0
