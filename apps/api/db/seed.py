import asyncio

from sqlalchemy import select

from core.config import settings
from core.security import hash_password
from db.base import Base
from db.session import engine, async_session_maker
from models.asset import Asset
from models.asset_fingerprint import AssetFingerprint
from models.organization import Organization
from models.user import User


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_demo_data():
    """Seed demo data for testing and development."""
    async with async_session_maker() as session:
        # Check if demo org already exists
        existing = await session.scalar(
            select(Organization).where(Organization.name == "Demo Sports League")
        )
        if existing:
            print("Demo data already exists, skipping seed")
            return

        # Create demo organization
        org = Organization(name="Demo Sports League", plan="pro")
        session.add(org)
        await session.flush()

        # Create demo user
        user = User(
            org_id=org.id,
            email="admin@demo.com",
            hashed_password=hash_password("demo123"),
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # Create demo assets with fingerprints
        demo_assets = [
            Asset(
                id="11111111-1111-1111-1111-111111111111",
                org_id=org.id,
                title="Champions League Final 2024",
                content_type="video",
                territories=["US", "UK", "EU"],
                status="protected",
            ),
            Asset(
                id="22222222-2222-2222-2222-222222222222",
                org_id=org.id,
                title="Top 10 Goals of the Season",
                content_type="video",
                territories=["US", "UK"],
                status="protected",
            ),
            Asset(
                id="33333333-3333-3333-3333-333333333333",
                org_id=org.id,
                title="Press Conference Highlights",
                content_type="video",
                territories=["US"],
                status="protected",
            ),
        ]
        session.add_all(demo_assets)
        await session.flush()

        # Add fingerprints
        for asset in demo_assets:
            fp = AssetFingerprint(
                asset_id=asset.id,
                phash="abc123def456",
                whash="def456abc123",
                watermark_payload="DEMO0001",
            )
            session.add(fp)

        # Create demo violations
        from datetime import datetime, timezone
        from models.violation import Violation

        violations = [
            Violation(
                id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                asset_id=demo_assets[0].id,
                discovered_url="https://example.com/pirated-video-1",
                platform="YouTube",
                status="suspected",
                confidence=0.92,
                infringement_type="exact_copy",
                transformation_types=["re_encoded"],
                estimated_reach=50000,
                detected_at=datetime.now(timezone.utc),
            ),
            Violation(
                id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                asset_id=demo_assets[1].id,
                discovered_url="https://streamingsite.net/clips/goals",
                platform="Custom",
                status="confirmed",
                confidence=0.87,
                infringement_type="re_encoded",
                transformation_types=["re_encoded", "watermark_removed"],
                estimated_reach=25000,
                detected_at=datetime.now(timezone.utc),
            ),
        ]
        session.add_all(violations)

        await session.commit()
        print("Demo data seeded successfully")


async def main():
    await create_tables()
    if settings.app_env != "production":
        await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())