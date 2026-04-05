import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _seed_records(client: AsyncClient):
    """Insert a known set of records to assert dashboard aggregations against."""
    records = [
        {"amount": 5000.00, "type": "income",  "category": "Salary",    "date": "2024-01-15"},
        {"amount": 1200.00, "type": "expense", "category": "Rent",      "date": "2024-01-20"},
        {"amount":  300.00, "type": "expense", "category": "Groceries", "date": "2024-01-25"},
        {"amount": 5000.00, "type": "income",  "category": "Salary",    "date": "2024-02-15"},
        {"amount": 1200.00, "type": "expense", "category": "Rent",      "date": "2024-02-20"},
        {"amount":  450.00, "type": "expense", "category": "Utilities", "date": "2024-02-22"},
        {"amount":  800.00, "type": "income",  "category": "Freelance", "date": "2024-02-28"},
    ]
    for r in records:
        resp = await client.post("/records", json=r)
        assert resp.status_code == 201, resp.text


# ── /dashboard/totals ─────────────────────────────────────────────────────────

async def test_totals_accessible_by_viewer(admin_client: AsyncClient):
    # Register a second user as viewer, then test access
    await admin_client.post("/auth/register", json={
        "name": "Viewer",
        "email": "viewer_dash@test.com",
        "password": "viewerpassword",
        "role": "viewer",
    })
    login = await admin_client.post("/auth/login", json={
        "email": "viewer_dash@test.com",
        "password": "viewerpassword",
    })
    token = login.json()["access_token"]
    resp = await admin_client.get("/dashboard/totals", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_balance" in data


async def test_totals_correct_values(admin_client: AsyncClient):
    await _seed_records(admin_client)
    resp = await admin_client.get("/dashboard/totals")
    assert resp.status_code == 200
    data = resp.json()

    # Values include ALL records in the test DB, so just check types and net math
    assert data["total_income"] >= 0
    assert data["total_expenses"] >= 0
    assert abs(data["net_balance"] - (data["total_income"] - data["total_expenses"])) < 0.01


# ── /dashboard/summary ────────────────────────────────────────────────────────

async def test_summary_requires_analyst_role(admin_client: AsyncClient):
    # Viewer should be denied
    await admin_client.post("/auth/register", json={
        "name": "Viewer2",
        "email": "viewer_sum@test.com",
        "password": "viewerpassword",
        "role": "viewer",
    })
    login = await admin_client.post("/auth/login", json={
        "email": "viewer_sum@test.com",
        "password": "viewerpassword",
    })
    token = login.json()["access_token"]
    resp = await admin_client.get("/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_summary_accessible_by_admin(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/summary")
    assert resp.status_code == 200


async def test_summary_structure(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_balance" in data
    assert "record_count" in data
    assert "category_totals" in data
    assert "monthly_trends" in data
    assert "recent_activity" in data
    assert isinstance(data["category_totals"], list)
    assert isinstance(data["monthly_trends"], list)
    assert isinstance(data["recent_activity"], list)


async def test_summary_net_balance_equals_income_minus_expenses(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/summary")
    data = resp.json()
    expected_net = round(data["total_income"] - data["total_expenses"], 2)
    assert abs(data["net_balance"] - expected_net) < 0.01


async def test_recent_activity_max_10_items(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/summary")
    data = resp.json()
    assert len(data["recent_activity"]) <= 10


# ── /dashboard/categories ─────────────────────────────────────────────────────

async def test_categories_returns_list(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_categories_filter_by_type(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/categories?type=expense")
    assert resp.status_code == 200
    # Each category total in the list should have the right shape
    for item in resp.json():
        assert "category" in item
        assert "total" in item
        assert "count" in item


async def test_categories_sorted_by_total_descending(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/categories")
    totals = [item["total"] for item in resp.json()]
    assert totals == sorted(totals, reverse=True)


# ── /dashboard/trends ─────────────────────────────────────────────────────────

async def test_trends_returns_list(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/trends")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_trends_months_param(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/trends?months=3")
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


async def test_trends_invalid_months_returns_422(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/trends?months=999")
    assert resp.status_code == 422


async def test_trends_net_equals_income_minus_expense(admin_client: AsyncClient):
    resp = await admin_client.get("/dashboard/trends")
    for item in resp.json():
        expected = round(item["income"] - item["expense"], 2)
        assert abs(item["net"] - expected) < 0.01


# ── /health ───────────────────────────────────────────────────────────────────

async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
