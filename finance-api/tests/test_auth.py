import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_first_user_becomes_admin(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "name": "First User",
        "email": "first@test.com",
        "password": "securepass1",
        "role": "viewer",   # ignored — first user is always admin
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "admin"
    assert data["status"] == "active"
    assert "password_hash" not in data


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"name": "User A", "email": "dupetest@test.com", "password": "password123", "role": "viewer"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


async def test_register_short_password_returns_422(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "name": "User B",
        "email": "shortpw@test.com",
        "password": "123",
        "role": "viewer",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post("/auth/register", json={
        "name": "Login User",
        "email": "loginuser@test.com",
        "password": "password123",
        "role": "viewer",
    })
    resp = await client.post("/auth/login", json={
        "email": "loginuser@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@test.com"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/auth/register", json={
        "name": "Wrong PW User",
        "email": "wrongpw@test.com",
        "password": "correctpassword",
        "role": "viewer",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_login_nonexistent_email_returns_401(client: AsyncClient):
    resp = await client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "password123",
    })
    assert resp.status_code == 401


async def test_protected_route_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_protected_route_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


async def test_get_me_returns_current_user(admin_client: AsyncClient):
    resp = await admin_client.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"
