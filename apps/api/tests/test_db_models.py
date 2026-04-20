import pytest
from sqlalchemy import text

from models.organization import Organization
from models.asset import Asset
from models.asset_fingerprint import AssetFingerprint
from models.violation import Violation
from models.dmca_notice import DMCANotice
from models.task import Task
from models.scan_run import ScanRun

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

@pytest.mark.asyncio
async def test_create_asset_fingerprint(db_session):
    org = Organization(name="Org", plan="free")
    db_session.add(org)
    await db_session.flush()
    asset = Asset(org_id=org.id, title="Match", content_type="video", territories=[])
    db_session.add(asset)
    await db_session.flush()
    fp = AssetFingerprint(asset_id=asset.id, phash="a" * 64, whash="b" * 64)
    db_session.add(fp)
    await db_session.commit()
    await db_session.refresh(fp)
    assert fp.asset_id == asset.id
    assert fp.phash == "a" * 64
    assert fp.whash == "b" * 64
    assert fp.fingerprinted_at is None

@pytest.mark.asyncio
async def test_create_violation(db_session):
    org = Organization(name="Org2", plan="free")
    db_session.add(org)
    await db_session.flush()
    asset = Asset(org_id=org.id, title="Game", content_type="video", territories=[])
    db_session.add(asset)
    await db_session.flush()
    v = Violation(
        asset_id=asset.id,
        discovered_url="https://example.com/stolen",
        platform="youtube",
        confidence=0.95,
        infringement_type="exact_copy",
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    assert v.status == "suspected"
    assert v.confidence == 0.95
    assert v.transformation_types == []
    assert v.rights_territory_violation is False
    assert v.detected_at is not None

@pytest.mark.asyncio
async def test_create_dmca_notice(db_session):
    org = Organization(name="Org3", plan="free")
    db_session.add(org)
    await db_session.flush()
    asset = Asset(org_id=org.id, title="Clip", content_type="video", territories=[])
    db_session.add(asset)
    await db_session.flush()
    v = Violation(
        asset_id=asset.id,
        discovered_url="https://pirate.example/clip",
        platform="twitter",
        confidence=0.80,
        infringement_type="partial_clip",
    )
    db_session.add(v)
    await db_session.flush()
    notice = DMCANotice(
        violation_id=v.id,
        notice_text="DMCA takedown notice for unauthorized use.",
    )
    db_session.add(notice)
    await db_session.commit()
    await db_session.refresh(notice)
    assert notice.id is not None
    assert notice.status == "draft"
    assert notice.sent_at is None


@pytest.mark.asyncio
async def test_create_task(db_session):
    import uuid
    t = Task(
        id=str(uuid.uuid4()),
        type="fingerprint",
        status="queued",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    assert t.status == "queued"
    assert t.result is None

@pytest.mark.asyncio
async def test_create_scan_run(db_session):
    org = Organization(name="Org4", plan="free")
    db_session.add(org)
    await db_session.flush()
    asset = Asset(org_id=org.id, title="Event", content_type="video", territories=[])
    db_session.add(asset)
    await db_session.flush()
    run = ScanRun(asset_id=asset.id, status="running")
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)
    assert run.id is not None
    assert run.violations_found == 0
    assert run.errors is None
