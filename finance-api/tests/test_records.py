import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SAMPLE_RECORD = {
    "amount": 1500.00,
    "type": "income",
    "category": "Salary",
    "date": "2024-03-15",
    "notes": "March salary",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _create_record(client: AsyncClient, overrides: dict = {}) -> dict:
    resp = await client.post("/records", json={**SAMPLE_RECORD, **overrides})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _viewer_client(client: AsyncClient) -> AsyncClient:
    """Returns a client authenticated as a viewer."""
    await client.post("/auth/register", json={
        "name": "Viewer User",
        "email": "viewer_rec@test.com",
        "password": "viewerpassword",
        "role": "viewer",
    })
    resp = await client.post("/auth/login", json={
        "email": "viewer_rec@test.com",
        "password": "viewerpassword",
    })
    c = client
    c.headers = {**c.headers, "Authorization": f"Bearer {resp.json()['access_token']}"}
    return c


# ── Create ─────────────────────────────────────────────────────────────────────

async def test_admin_can_create_record(admin_client: AsyncClient):
    record = await _create_record(admin_client)
    assert record["amount"] == 1500.00
    assert record["type"] == "income"
    assert record["category"] == "Salary"
    assert record["date"] == "2024-03-15"
    assert "id" in record


async def test_create_record_negative_amount_returns_422(admin_client: AsyncClient):
    resp = await admin_client.post("/records", json={**SAMPLE_RECORD, "amount": -100})
    assert resp.status_code == 422


async def test_create_record_invalid_date_returns_422(admin_client: AsyncClient):
    resp = await admin_client.post("/records", json={**SAMPLE_RECORD, "date": "15-03-2024"})
    assert resp.status_code == 422


async def test_create_record_invalid_type_returns_422(admin_client: AsyncClient):
    resp = await admin_client.post("/records", json={**SAMPLE_RECORD, "type": "transfer"})
    assert resp.status_code == 422


async def test_viewer_cannot_create_record(admin_client: AsyncClient):
    # Register a viewer (second user, so role is respected)
    await admin_client.post("/auth/register", json={
        "name": "Viewer",
        "email": "viewer_create@test.com",
        "password": "viewerpassword",
        "role": "viewer",
    })
    login = await admin_client.post("/auth/login", json={
        "email": "viewer_create@test.com",
        "password": "viewerpassword",
    })
    token = login.json()["access_token"]
    resp = await admin_client.post(
        "/records",
        json=SAMPLE_RECORD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── Read ───────────────────────────────────────────────────────────────────────

async def test_list_records_returns_paginated(admin_client: AsyncClient):
    for i in range(3):
        await _create_record(admin_client, {"category": f"Cat{i}", "amount": float(100 + i)})

    resp = await admin_client.get("/records?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "total_pages" in data
    assert isinstance(data["items"], list)


async def test_get_record_by_id(admin_client: AsyncClient):
    record = await _create_record(admin_client)
    resp = await admin_client.get(f"/records/{record['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == record["id"]


async def test_get_nonexistent_record_returns_404(admin_client: AsyncClient):
    resp = await admin_client.get("/records/nonexistent-id")
    assert resp.status_code == 404


# ── Filter ─────────────────────────────────────────────────────────────────────

async def test_filter_by_type(admin_client: AsyncClient):
    await _create_record(admin_client, {"type": "income",  "category": "FilterIncome",  "date": "2024-01-01"})
    await _create_record(admin_client, {"type": "expense", "category": "FilterExpense", "date": "2024-01-02"})

    resp = await admin_client.get("/records?type=income")
    assert resp.status_code == 200
    assert all(r["type"] == "income" for r in resp.json()["items"])


async def test_filter_by_date_range(admin_client: AsyncClient):
    await _create_record(admin_client, {"date": "2024-06-01", "category": "June"})
    await _create_record(admin_client, {"date": "2024-07-01", "category": "July"})
    await _create_record(admin_client, {"date": "2024-08-01", "category": "August"})

    resp = await admin_client.get("/records?date_from=2024-06-01&date_to=2024-07-31")
    assert resp.status_code == 200
    for r in resp.json()["items"]:
        assert "2024-06-01" <= r["date"] <= "2024-07-31"


async def test_filter_by_category(admin_client: AsyncClient):
    await _create_record(admin_client, {"category": "Groceries"})
    resp = await admin_client.get("/records?category=Grocer")
    assert resp.status_code == 200
    assert all("grocer" in r["category"].lower() for r in resp.json()["items"])


# ── Update ─────────────────────────────────────────────────────────────────────

async def test_admin_can_update_record(admin_client: AsyncClient):
    record = await _create_record(admin_client)
    resp = await admin_client.patch(f"/records/{record['id']}", json={"amount": 2000.00, "notes": "Updated"})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["amount"] == 2000.00
    assert updated["notes"] == "Updated"


async def test_update_with_no_fields_returns_400(admin_client: AsyncClient):
    record = await _create_record(admin_client)
    resp = await admin_client.patch(f"/records/{record['id']}", json={})
    assert resp.status_code == 400


async def test_update_nonexistent_record_returns_404(admin_client: AsyncClient):
    resp = await admin_client.patch("/records/bad-id", json={"amount": 500})
    assert resp.status_code == 404


# ── Delete (soft) ──────────────────────────────────────────────────────────────

async def test_admin_can_soft_delete_record(admin_client: AsyncClient):
    record = await _create_record(admin_client, {"category": "ToDelete"})
    del_resp = await admin_client.delete(f"/records/{record['id']}")
    assert del_resp.status_code == 204

    # Deleted record should no longer appear
    get_resp = await admin_client.get(f"/records/{record['id']}")
    assert get_resp.status_code == 404


async def test_delete_nonexistent_record_returns_404(admin_client: AsyncClient):
    resp = await admin_client.delete("/records/ghost-id")
    assert resp.status_code == 404
