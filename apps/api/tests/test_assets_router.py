import uuid

import pytest

from core.security import create_access_token


def _make_token(user_id: str, org_id: str) -> str:
    return create_access_token(user_id, org_id)


@pytest.mark.asyncio
async def test_list_assets_returns_empty_for_new_org(client):
    reg = await client.post(
        "/auth/register",
        json={"org_name": "Asset Org", "email": "assetuser@sportsnet.com", "password": "securepass123"},
    )
    token = reg.json()["data"]["access_token"]
    resp = await client.get("/api/v1/assets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_asset_not_found(client):
    reg = await client.post(
        "/auth/register",
        json={"org_name": "Asset Org 2", "email": "assetuser2@sportsnet.com", "password": "securepass123"},
    )
    token = reg.json()["data"]["access_token"]
    random_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/assets/{random_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assets_requires_auth(client):
    resp = await client.get("/api/v1/assets")
    assert resp.status_code == 403
