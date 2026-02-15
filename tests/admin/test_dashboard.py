"""Integration tests for admin dashboard GET /api/v1/admin/dashboard."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_dashboard_returns_200_and_summary(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/admin/dashboard with admin auth returns 200 and summary fields."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    summary = data["summary"]
    assert "activeClients" in summary
    assert "auditsInLast30Days" in summary
    assert "totalCompletedWorkflows" in summary
    assert "passRate" in summary
    assert isinstance(summary["activeClients"], int)
    assert isinstance(summary["auditsInLast30Days"], int)
    assert isinstance(summary["totalCompletedWorkflows"], int)
    assert isinstance(summary["passRate"], int)
    assert summary["activeClients"] >= 0
    assert summary["auditsInLast30Days"] >= 0
    assert summary["totalCompletedWorkflows"] >= 0
    assert 0 <= summary["passRate"] <= 100


@pytest.mark.asyncio
async def test_admin_dashboard_non_admin_returns_403(
    client: AsyncClient, non_admin_headers: dict
):
    """GET /api/v1/admin/dashboard with non-admin auth returns 403."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=non_admin_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_dashboard_certification_breakdown(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/admin/dashboard as admin returns certificationBreakdown (bronze, silver, gold)."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "certificationBreakdown" in data
    cb = data["certificationBreakdown"]
    assert "bronze" in cb
    assert "silver" in cb
    assert "gold" in cb
    assert isinstance(cb["bronze"], int)
    assert isinstance(cb["silver"], int)
    assert isinstance(cb["gold"], int)
    assert cb["bronze"] >= 0
    assert cb["silver"] >= 0
    assert cb["gold"] >= 0


@pytest.mark.asyncio
async def test_admin_dashboard_recent_workflows(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/admin/dashboard as admin returns recentWorkflows list (at most 10)."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "recentWorkflows" in data
    assert isinstance(data["recentWorkflows"], list)
    assert len(data["recentWorkflows"]) <= 10
    for item in data["recentWorkflows"]:
        assert "workflowId" in item
        assert "auditId" in item
        assert "status" in item
        assert "updatedAt" in item


@pytest.mark.asyncio
async def test_admin_dashboard_contract_response_shape(
    client: AsyncClient, admin_headers: dict
):
    """Response shape matches OpenAPI AdminDashboardResponse (contract test)."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Required top-level
    assert "summary" in data
    assert "certificationBreakdown" in data
    assert "recentWorkflows" in data
    # Summary
    assert "activeClients" in data["summary"]
    assert "auditsInLast30Days" in data["summary"]
    assert "totalCompletedWorkflows" in data["summary"]
    assert "passRate" in data["summary"]
    # CertificationBreakdown
    assert "bronze" in data["certificationBreakdown"]
    assert "silver" in data["certificationBreakdown"]
    assert "gold" in data["certificationBreakdown"]
    # RecentWorkflowItem
    for w in data["recentWorkflows"]:
        assert "workflowId" in w
        assert "auditId" in w
        assert "status" in w
        assert "updatedAt" in w


@pytest.mark.asyncio
async def test_admin_dashboard_empty_data_returns_200(
    client: AsyncClient, admin_headers: dict
):
    """With no brands/audits/workflows, dashboard returns 200 with all metrics 0 and recentWorkflows [] (FR-008)."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Empty state: all numeric metrics can be 0, recentWorkflows []
    assert data["summary"]["activeClients"] >= 0
    assert data["summary"]["auditsInLast30Days"] >= 0
    assert data["summary"]["totalCompletedWorkflows"] >= 0
    assert 0 <= data["summary"]["passRate"] <= 100
    assert data["certificationBreakdown"]["bronze"] >= 0
    assert data["certificationBreakdown"]["silver"] >= 0
    assert data["certificationBreakdown"]["gold"] >= 0
    assert isinstance(data["recentWorkflows"], list)
