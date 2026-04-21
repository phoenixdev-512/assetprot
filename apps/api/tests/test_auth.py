import pytest

REGISTER_PAYLOAD = {
    "org_name": "Sports Network",
    "email": "admin@sportsnet.com",
    "password": "securepass123",
}


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_success(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    refresh_token = reg.json()["data"]["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]


@pytest.mark.asyncio
async def test_refresh_with_access_token(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    access_token = reg.json()["data"]["access_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


@pytest.mark.asyncio
async def test_me_authenticated(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    access_token = reg.json()["data"]["access_token"]
    resp = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["is_active"] is True
    assert "id" in data
    assert "org_id" in data


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403
