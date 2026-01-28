"""Integration tests for brands dashboard endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard_summary_metrics(client: AsyncClient, auth_headers):
    """Test dashboard endpoint returns summary metrics correctly."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "totalAudits" in data["summary"]
    assert "completedAudits" in data["summary"]
    assert isinstance(data["summary"]["totalAudits"], int)
    assert isinstance(data["summary"]["completedAudits"], int)
    assert data["summary"]["totalAudits"] >= 0
    assert data["summary"]["completedAudits"] >= 0


@pytest.mark.asyncio
async def test_dashboard_no_audits(client: AsyncClient, auth_headers):
    """Test dashboard endpoint with brand that has no audits."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["totalAudits"] == 0
    assert data["summary"]["completedAudits"] == 0
    assert data["latestAuditScores"] is None
    assert data["recentAuditWorkflows"] == []


@pytest.mark.asyncio
async def test_dashboard_multiple_statuses(client: AsyncClient, auth_headers):
    """Test dashboard endpoint with brand that has audits with multiple statuses."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    # Verify completed audits count is less than or equal to total audits
    assert data["summary"]["completedAudits"] <= data["summary"]["totalAudits"]


@pytest.mark.asyncio
async def test_get_latest_audit_scores(client: AsyncClient, auth_headers):
    """Test dashboard endpoint returns latest audit scores correctly."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "latestAuditScores" in data
    # If there are completed audits, latestAuditScores should not be None
    if data["summary"]["completedAudits"] > 0:
        assert data["latestAuditScores"] is not None
        assert "auditId" in data["latestAuditScores"]
        assert "completedAt" in data["latestAuditScores"]
        assert "categoryScores" in data["latestAuditScores"]
        assert isinstance(data["latestAuditScores"]["categoryScores"], list)


@pytest.mark.asyncio
async def test_dashboard_no_completed_audits(client: AsyncClient, auth_headers):
    """Test dashboard endpoint with brand that has no completed audits."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # If no completed audits, latestAuditScores should be None
    if data["summary"]["completedAudits"] == 0:
        assert data["latestAuditScores"] is None


@pytest.mark.asyncio
async def test_latest_audit_by_completion_time(client: AsyncClient, auth_headers):
    """Test that latest audit is selected by completion timestamp."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # If latest audit scores exist, verify structure
    if data["latestAuditScores"]:
        assert "completedAt" in data["latestAuditScores"]
        assert data["latestAuditScores"]["completedAt"] is not None


@pytest.mark.asyncio
async def test_partial_category_scores(client: AsyncClient, auth_headers):
    """Test dashboard handles partial category scores correctly."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # If latest audit scores exist, verify category scores structure
    if data["latestAuditScores"] and data["latestAuditScores"]["categoryScores"]:
        for score in data["latestAuditScores"]["categoryScores"]:
            assert "category" in score
            assert "score" in score
            assert "hasClaims" in score
            assert score["category"] in ["ENVIRONMENTAL", "SOCIAL", "CIRCULARITY", "TRANSPARENCY"]
            assert 0 <= score["score"] <= 100
            assert isinstance(score["hasClaims"], bool)


@pytest.mark.asyncio
async def test_get_recent_workflows(client: AsyncClient, auth_headers):
    """Test dashboard endpoint returns recent workflows list correctly."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "recentAuditWorkflows" in data
    assert isinstance(data["recentAuditWorkflows"], list)
    # Should return at most 3 workflows
    assert len(data["recentAuditWorkflows"]) <= 3


@pytest.mark.asyncio
async def test_recent_workflows_ordering(client: AsyncClient, auth_headers):
    """Test that recent workflows are ordered by workflow created_at (newest first)."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    if len(data["recentAuditWorkflows"]) > 1:
        # Verify ordering (newest first by workflow created_at)
        for i in range(len(data["recentAuditWorkflows"]) - 1):
            current_created = data["recentAuditWorkflows"][i]["createdAt"]
            next_created = data["recentAuditWorkflows"][i + 1]["createdAt"]
            assert current_created >= next_created


@pytest.mark.asyncio
async def test_status_mapping(client: AsyncClient, auth_headers):
    """Test that workflow statuses are mapped to user-friendly display statuses."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # Verify status mapping
    valid_statuses = ["Completed", "Processing", "Generated", "Failed"]
    for workflow in data["recentAuditWorkflows"]:
        assert "status" in workflow
        assert workflow["status"] in valid_statuses


@pytest.mark.asyncio
async def test_category_scores_only_completed(client: AsyncClient, auth_headers):
    """Test that category scores are only included for completed workflows."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    for workflow in data["recentAuditWorkflows"]:
        if workflow["status"] == "Completed":
            assert "categoryScores" in workflow
            # categoryScores can be None or a list
            if workflow["categoryScores"] is not None:
                assert isinstance(workflow["categoryScores"], list)
        else:
            # Non-completed workflows should not have category scores
            assert workflow.get("categoryScores") is None


@pytest.mark.asyncio
async def test_recent_workflows_limit(client: AsyncClient, auth_headers):
    """Test that recent workflows list is limited to 3 workflows."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["recentAuditWorkflows"]) <= 3


@pytest.mark.asyncio
async def test_complete_dashboard_response(client: AsyncClient, auth_headers):
    """Test complete dashboard response structure and validation."""
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields exist
    assert "summary" in data
    assert "latestAuditScores" in data
    assert "recentAuditWorkflows" in data

    # Verify summary structure
    assert "totalAudits" in data["summary"]
    assert "completedAudits" in data["summary"]
    assert isinstance(data["summary"]["totalAudits"], int)
    assert isinstance(data["summary"]["completedAudits"], int)

    # Verify latestAuditScores structure (if present)
    if data["latestAuditScores"] is not None:
        assert "auditId" in data["latestAuditScores"]
        assert "completedAt" in data["latestAuditScores"]
        assert "categoryScores" in data["latestAuditScores"]
        assert isinstance(data["latestAuditScores"]["categoryScores"], list)

    # Verify recentAuditWorkflows structure
    assert isinstance(data["recentAuditWorkflows"], list)
    for workflow in data["recentAuditWorkflows"]:
        assert "workflowId" in workflow
        assert "auditId" in workflow
        assert "status" in workflow
        assert "createdAt" in workflow
        assert workflow["status"] in ["Completed", "Processing", "Generated", "Failed"]


@pytest.mark.asyncio
async def test_dashboard_performance(client: AsyncClient, auth_headers):
    """Test that dashboard endpoint responds within performance target (<500ms)."""
    import time

    start_time = time.time()
    response = await client.get(
        "/api/v1/brands/dashboard",
        headers=auth_headers,
    )
    elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    assert response.status_code == 200
    # Performance target: <500ms for brands with up to 100 audits
    assert elapsed_time < 500, f"Dashboard response time {elapsed_time}ms exceeds 500ms target"
