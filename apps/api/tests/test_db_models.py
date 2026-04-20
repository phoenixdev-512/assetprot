import pytest
from sqlalchemy import text

from models.organization import Organization
from models.asset import Asset

@pytest.mark.asyncio
async def test_db_session_connects(db_session):
    result = await db_session.execute(text("SELECT 1"))
    row = result.scalar()
    assert row == 1

@pytest.mark.asyncio
async def test_create_organization(db_session):
    org = Organization(name="Test Sports Network", plan="pro")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    assert org.id is not None
    assert org.name == "Test Sports Network"

@pytest.mark.asyncio
async def test_create_asset(db_session):
    org = Organization(name="Sports Co", plan="free")
    db_session.add(org)
    await db_session.flush()
    asset = Asset(
        org_id=org.id,
        title="Championship Highlights",
        content_type="video",
        territories=["US", "GB"],
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    assert asset.id is not None
    assert asset.status == "pending"
