# GUARDIAN Phase 1: Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the complete GUARDIAN infrastructure — Docker Compose stack (PostgreSQL 16, Redis 7, Qdrant, FastAPI API, Next.js Web, Celery Worker), all seven SQLAlchemy ORM models, Alembic migrations, and a minimal `/health` endpoint that proves the full stack is wired.

**Architecture:** Foundation-first vertical slice. Phase 1 produces a running `docker compose up --build` with all tables migrated and `GET /health` returning 200. Zero business logic — only the plumbing every future phase depends on. Subsequent phases (Backend Core, Fingerprinting, Frontend Slice 1, Agents, Triage+DMCA) each get their own plan after this one is verified.

**Tech Stack:** Docker Compose, PostgreSQL 16, Redis 7, Qdrant v1.11, FastAPI 0.115, SQLAlchemy 2.0 async, Alembic 1.13, asyncpg, Next.js 14, Tailwind CSS, Celery 5

---

## File Map

```
guardian/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── apps/
│   ├── api/
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   ├── alembic.ini
│   │   ├── celery_app.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   │       ├── env.py
│   │   │       ├── script.py.mako
│   │   │       └── versions/
│   │   │           └── 0001_initial_schema.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── organization.py
│   │   │   ├── asset.py
│   │   │   ├── asset_fingerprint.py
│   │   │   ├── violation.py
│   │   │   ├── dmca_notice.py
│   │   │   ├── task.py
│   │   │   └── scan_run.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── conftest.py
│   │       └── test_db_models.py
│   └── web/
│       ├── package.json
│       ├── next.config.ts
│       ├── tsconfig.json
│       ├── tailwind.config.ts
│       ├── postcss.config.mjs
│       └── src/app/
│           ├── layout.tsx
│           └── page.tsx
└── infrastructure/
    └── docker/
        ├── api.Dockerfile
        └── web.Dockerfile
```

---

## Task 1: Project scaffolding + .gitignore

**Files:**
- Create: `.gitignore`
- Create: `apps/api/tests/__init__.py`
- Create: `apps/api/models/__init__.py`
- Create: `apps/api/core/__init__.py`
- Create: `apps/api/db/__init__.py`
- Create: `apps/api/db/migrations/versions/` (empty dir placeholder)

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p apps/api/core apps/api/db/migrations/versions apps/api/models apps/api/tests
mkdir -p apps/web/src/app infrastructure/docker docs/superpowers/plans docs/superpowers/specs
touch apps/api/core/__init__.py apps/api/db/__init__.py apps/api/models/__init__.py apps/api/tests/__init__.py
```

- [ ] **Step 2: Write pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

Save to: `apps/api/pytest.ini`

- [ ] **Step 3: Write .gitignore**

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
.next/
out/

# Env
.env
.env.local
.env.*.local

# Docker
*.log

# OS
.DS_Store
Thumbs.db
```

Save to: `.gitignore`

- [ ] **Step 4: Commit**

```bash
git init
git add .gitignore apps/api/pytest.ini apps/api/core/__init__.py apps/api/db/__init__.py apps/api/models/__init__.py apps/api/tests/__init__.py
git commit -m "chore: scaffold project directory structure"
```

---

## Task 2: Environment configuration

**Files:**
- Create: `.env.example`
- Create: `apps/api/core/config.py`
- Create: `apps/api/requirements.txt`
- Create: `apps/api/requirements-dev.txt`

- [ ] **Step 1: Write .env.example**

```bash
# PostgreSQL
POSTGRES_PASSWORD=changeme_dev
DATABASE_URL=postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=changeme_dev

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# JWT — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=changeme_generate_a_real_secret

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# App
APP_ENV=development
```

Save to: `.env.example`

- [ ] **Step 2: Write requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
alembic==1.13.3
asyncpg==0.29.0
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
redis==5.1.1
celery==5.4.0
qdrant-client==1.11.3
httpx==0.27.2
anthropic==0.37.1
```

Save to: `apps/api/requirements.txt`

- [ ] **Step 3: Write requirements-dev.txt**

```
-r requirements.txt
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
```

Save to: `apps/api/requirements-dev.txt`

- [ ] **Step 4: Write core/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str
    qdrant_url: str
    qdrant_api_key: str
    anthropic_api_key: str
    jwt_secret_key: str
    celery_broker_url: str
    celery_result_backend: str
    app_env: str = "development"


settings = Settings()
```

Save to: `apps/api/core/config.py`

- [ ] **Step 5: Commit**

```bash
git add .env.example apps/api/requirements.txt apps/api/requirements-dev.txt apps/api/core/config.py
git commit -m "chore: add environment config and Python requirements"
```

---

## Task 3: SQLAlchemy base + session factory

**Files:**
- Create: `apps/api/db/base.py`
- Create: `apps/api/db/session.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_db_models.py
import pytest
from sqlalchemy import text

@pytest.mark.asyncio
async def test_db_session_connects(db_session):
    result = await db_session.execute(text("SELECT 1"))
    row = result.scalar()
    assert row == 1
```

Save to: `apps/api/tests/test_db_models.py`

- [ ] **Step 2: Write conftest.py**

```python
# apps/api/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

Save to: `apps/api/tests/conftest.py`

- [ ] **Step 3: Run test — expect ImportError (db.base not yet defined)**

```bash
cd apps/api && pip install -r requirements-dev.txt
pytest tests/test_db_models.py::test_db_session_connects -v
```

Expected: `ModuleNotFoundError: No module named 'db.base'`

- [ ] **Step 4: Write db/base.py**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Save to: `apps/api/db/base.py`

- [ ] **Step 5: Write db/session.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

engine = create_async_engine(settings.database_url, echo=settings.app_env == "development")
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
```

Save to: `apps/api/db/session.py`

- [ ] **Step 6: Run test — expect PASS**

```bash
cd apps/api && pytest tests/test_db_models.py::test_db_session_connects -v
```

Expected: `PASSED`

- [ ] **Step 7: Commit**

```bash
git add apps/api/db/base.py apps/api/db/session.py apps/api/tests/conftest.py apps/api/tests/test_db_models.py
git commit -m "feat: add SQLAlchemy async base and session factory"
```

---

## Task 4: ORM models — organizations + assets

**Files:**
- Create: `apps/api/models/organization.py`
- Create: `apps/api/models/asset.py`
- Modify: `apps/api/models/__init__.py`

- [ ] **Step 1: Add failing tests**

Append to `apps/api/tests/test_db_models.py`:

```python
from models.organization import Organization
from models.asset import Asset
import uuid

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
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd apps/api && pytest tests/test_db_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'models.organization'`

- [ ] **Step 3: Write models/organization.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="organization")
```

Save to: `apps/api/models/organization.py`

- [ ] **Step 4: Write models/asset.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)  # video | image | audio
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    # pending | fingerprinting | fingerprint_partial | protected | failed
    rights_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    territories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="assets")
    fingerprint: Mapped["AssetFingerprint | None"] = relationship("AssetFingerprint", back_populates="asset", uselist=False)
    violations: Mapped[list["Violation"]] = relationship("Violation", back_populates="asset")
    scan_runs: Mapped[list["ScanRun"]] = relationship("ScanRun", back_populates="asset")
```

Save to: `apps/api/models/asset.py`

- [ ] **Step 5: Update models/__init__.py**

```python
from models.organization import Organization
from models.asset import Asset

__all__ = ["Organization", "Asset"]
```

Save to: `apps/api/models/__init__.py`

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd apps/api && pytest tests/test_db_models.py -v
```

Expected: `test_db_session_connects PASSED`, `test_create_organization PASSED`, `test_create_asset PASSED`

- [ ] **Step 7: Commit**

```bash
git add apps/api/models/organization.py apps/api/models/asset.py apps/api/models/__init__.py apps/api/tests/test_db_models.py
git commit -m "feat: add Organization and Asset ORM models"
```

---

## Task 5: ORM models — asset_fingerprints + violations + dmca_notices

**Files:**
- Create: `apps/api/models/asset_fingerprint.py`
- Create: `apps/api/models/violation.py`
- Create: `apps/api/models/dmca_notice.py`
- Modify: `apps/api/models/__init__.py`

- [ ] **Step 1: Add failing tests**

Append to `apps/api/tests/test_db_models.py`:

```python
from models.asset_fingerprint import AssetFingerprint
from models.violation import Violation
from models.dmca_notice import DMCANotice

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
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd apps/api && pytest tests/test_db_models.py::test_create_asset_fingerprint -v
```

Expected: `ModuleNotFoundError: No module named 'models.asset_fingerprint'`

- [ ] **Step 3: Write models/asset_fingerprint.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class AssetFingerprint(Base):
    __tablename__ = "asset_fingerprints"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True
    )
    phash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    whash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    chromaprint: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    watermark_payload: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_vector_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fingerprinted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="fingerprint")
```

Save to: `apps/api/models/asset_fingerprint.py`

- [ ] **Step 4: Write models/violation.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    discovered_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="suspected")
    # suspected | confirmed | dismissed | dmca_sent | requires_human_review
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    infringement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # exact_copy | re_encoded | partial_clip | audio_only | false_positive
    transformation_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    estimated_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rights_territory_violation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triage_verdict: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="violations")
    dmca_notices: Mapped[list["DMCANotice"]] = relationship("DMCANotice", back_populates="violation")
```

Save to: `apps/api/models/violation.py`

- [ ] **Step 5: Write models/dmca_notice.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class DMCANotice(Base):
    __tablename__ = "dmca_notices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    violation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("violations.id", ondelete="CASCADE"), nullable=False
    )
    notice_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    # draft | sent | acknowledged | rejected
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    violation: Mapped["Violation"] = relationship("Violation", back_populates="dmca_notices")
```

Save to: `apps/api/models/dmca_notice.py`

- [ ] **Step 6: Update models/__init__.py**

```python
from models.organization import Organization
from models.asset import Asset
from models.asset_fingerprint import AssetFingerprint
from models.violation import Violation
from models.dmca_notice import DMCANotice

__all__ = ["Organization", "Asset", "AssetFingerprint", "Violation", "DMCANotice"]
```

- [ ] **Step 7: Run tests — expect all PASS**

```bash
cd apps/api && pytest tests/test_db_models.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 8: Commit**

```bash
git add apps/api/models/asset_fingerprint.py apps/api/models/violation.py apps/api/models/dmca_notice.py apps/api/models/__init__.py apps/api/tests/test_db_models.py
git commit -m "feat: add AssetFingerprint, Violation, and DMCANotice ORM models"
```

---

## Task 6: ORM models — tasks + scan_runs

**Files:**
- Create: `apps/api/models/task.py`
- Create: `apps/api/models/scan_run.py`
- Modify: `apps/api/models/__init__.py`

- [ ] **Step 1: Add failing tests**

Append to `apps/api/tests/test_db_models.py`:

```python
from models.task import Task
from models.scan_run import ScanRun

@pytest.mark.asyncio
async def test_create_task(db_session):
    t = Task(
        id=str(uuid.uuid4()),
        type="fingerprint",
        status="queued",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    assert t.status == "queued"

@pytest.mark.asyncio
async def test_create_scan_run(db_session):
    org = Organization(name="Org3", plan="free")
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
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd apps/api && pytest tests/test_db_models.py::test_create_task -v
```

Expected: `ModuleNotFoundError: No module named 'models.task'`

- [ ] **Step 3: Write models/task.py**

```python
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # = Celery task_id
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    # queued | running | complete | failed
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

Save to: `apps/api/models/task.py`

- [ ] **Step 4: Write models/scan_run.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    # running | complete | partial | failed
    violations_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset: Mapped["Asset"] = relationship("Asset", back_populates="scan_runs")
```

Save to: `apps/api/models/scan_run.py`

- [ ] **Step 5: Update models/__init__.py**

```python
from models.organization import Organization
from models.asset import Asset
from models.asset_fingerprint import AssetFingerprint
from models.violation import Violation
from models.dmca_notice import DMCANotice
from models.task import Task
from models.scan_run import ScanRun

__all__ = ["Organization", "Asset", "AssetFingerprint", "Violation", "DMCANotice", "Task", "ScanRun"]
```

- [ ] **Step 6: Run all model tests — expect 7 PASS**

```bash
cd apps/api && pytest tests/test_db_models.py -v
```

Expected: 7 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add apps/api/models/task.py apps/api/models/scan_run.py apps/api/models/__init__.py apps/api/tests/test_db_models.py
git commit -m "feat: add Task and ScanRun ORM models — all 7 models complete"
```

---

## Task 7: Alembic setup + initial migration

**Files:**
- Create: `apps/api/alembic.ini`
- Create: `apps/api/db/migrations/env.py`
- Create: `apps/api/db/migrations/script.py.mako`
- Create: `apps/api/db/migrations/versions/0001_initial_schema.py`

- [ ] **Step 1: Write alembic.ini**

```ini
[alembic]
script_location = db/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://placeholder

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Save to: `apps/api/alembic.ini`

- [ ] **Step 2: Write db/migrations/env.py**

```python
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from environment
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Import all models so Alembic can detect them
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from db.base import Base
import models  # noqa: F401 — registers all models with Base.metadata

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Save to: `apps/api/db/migrations/env.py`

- [ ] **Step 3: Write db/migrations/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

Save to: `apps/api/db/migrations/script.py.mako`

- [ ] **Step 4: Generate the initial migration**

Ensure PostgreSQL is running (see Task 9 for Docker Compose), then:

```bash
cd apps/api
export DATABASE_URL=postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian
alembic revision --autogenerate -m "initial_schema"
```

Expected: Creates `db/migrations/versions/<hash>_initial_schema.py` with all 7 tables.

Rename the generated file for clarity:
```bash
mv db/migrations/versions/*initial_schema.py db/migrations/versions/0001_initial_schema.py
```

Then open `0001_initial_schema.py` and verify it contains `op.create_table(...)` calls for all 7 tables:
- `organizations`
- `assets`
- `asset_fingerprints`
- `violations`
- `dmca_notices`
- `tasks`
- `scan_runs`

- [ ] **Step 5: Apply migration and verify tables exist**

```bash
cd apps/api
alembic upgrade head
```

Expected output ends with: `Running upgrade  -> 0001, initial_schema`

Verify tables:
```bash
psql postgresql://guardian:changeme_dev@localhost:5432/guardian -c "\dt"
```

Expected: 8 rows (7 tables + `alembic_version`)

- [ ] **Step 6: Add migration test**

Append to `apps/api/tests/test_db_models.py`:

```python
@pytest.mark.asyncio
async def test_all_seven_tables_exist(db_session):
    from sqlalchemy import text
    result = await db_session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    )
    tables = {row[0] for row in result.fetchall()}
    expected = {"organizations", "assets", "asset_fingerprints", "violations", "dmca_notices", "tasks", "scan_runs"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
```

- [ ] **Step 7: Run full test suite — expect 8 PASS**

```bash
cd apps/api && pytest tests/ -v --cov=. --cov-report=term-missing
```

Expected: 8 tests PASSED

- [ ] **Step 8: Commit**

```bash
git add apps/api/alembic.ini apps/api/db/migrations/ apps/api/tests/test_db_models.py
git commit -m "feat: add Alembic async migrations — initial schema with all 7 tables"
```

---

## Task 8: FastAPI app skeleton + /health endpoint

**Files:**
- Create: `apps/api/main.py`
- Create: `apps/api/celery_app.py`

- [ ] **Step 1: Add failing test**

Create `apps/api/tests/test_health.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
```

Save to: `apps/api/tests/test_health.py`

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd apps/api && pytest tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Write celery_app.py (stub)**

```python
from celery import Celery
from core.config import settings

celery_app = Celery(
    "guardian",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
```

Save to: `apps/api/celery_app.py`

- [ ] **Step 4: Write main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 3: load ML models into app.state here
    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "meta": {}}
```

Save to: `apps/api/main.py`

- [ ] **Step 5: Run test — expect PASS**

```bash
cd apps/api && pytest tests/test_health.py -v
```

Expected: `test_health_returns_ok PASSED`

- [ ] **Step 6: Run full test suite**

```bash
cd apps/api && pytest tests/ -v --cov=. --cov-report=term-missing
```

Expected: 9 tests PASSED, coverage reported

- [ ] **Step 7: Commit**

```bash
git add apps/api/main.py apps/api/celery_app.py apps/api/tests/test_health.py
git commit -m "feat: add FastAPI app skeleton with /health endpoint and Celery stub"
```

---

## Task 9: Docker Compose + Dockerfiles

**Files:**
- Create: `docker-compose.yml`
- Create: `infrastructure/docker/api.Dockerfile`
- Create: `infrastructure/docker/web.Dockerfile`

- [ ] **Step 1: Write infrastructure/docker/api.Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Save to: `infrastructure/docker/api.Dockerfile`

- [ ] **Step 2: Write infrastructure/docker/web.Dockerfile**

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

Save to: `infrastructure/docker/web.Dockerfile`

- [ ] **Step 3: Write docker-compose.yml**

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: guardian
      POSTGRES_USER: guardian
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U guardian"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.11.3
    ports:
      - "6333:6333"
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    volumes:
      - qdrant_data:/qdrant/storage

  api:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://guardian:${POSTGRES_PASSWORD}@postgres:5432/guardian
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/api:/app

  celery_worker:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
    command: celery -A celery_app worker --loglevel=info
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://guardian:${POSTGRES_PASSWORD}@postgres:5432/guardian
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/api:/app

  web:
    build:
      context: .
      dockerfile: infrastructure/docker/web.Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - api
    volumes:
      - ./apps/web:/app
      - /app/node_modules

volumes:
  postgres_data:
  qdrant_data:
```

Save to: `docker-compose.yml`

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml infrastructure/docker/api.Dockerfile infrastructure/docker/web.Dockerfile
git commit -m "feat: add Docker Compose with all 6 services and Dockerfiles"
```

---

## Task 10: Next.js web scaffold

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/tailwind.config.ts`
- Create: `apps/web/postcss.config.mjs`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Write package.json**

```json
{
  "name": "guardian-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "generate-types": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts"
  },
  "dependencies": {
    "next": "14.2.15",
    "react": "^18",
    "react-dom": "^18",
    "swr": "^2.2.5",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.2"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3.4.1",
    "postcss": "^8",
    "autoprefixer": "^10.0.1",
    "openapi-typescript": "^7.4.0"
  }
}
```

Save to: `apps/web/package.json`

- [ ] **Step 2: Write next.config.ts**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

Save to: `apps/web/next.config.ts`

- [ ] **Step 3: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Save to: `apps/web/tsconfig.json`

- [ ] **Step 4: Write tailwind.config.ts**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: { extend: {} },
  plugins: [],
};
export default config;
```

Save to: `apps/web/tailwind.config.ts`

- [ ] **Step 5: Write postcss.config.mjs**

```mjs
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
export default config;
```

Save to: `apps/web/postcss.config.mjs`

- [ ] **Step 6: Write src/app/layout.tsx**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GUARDIAN",
  description: "AI-native digital asset protection for sports media",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

Save to: `apps/web/src/app/layout.tsx`

- [ ] **Step 7: Write src/app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Save to: `apps/web/src/app/globals.css`

- [ ] **Step 8: Write src/app/page.tsx**

```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <h1 className="text-4xl font-bold">GUARDIAN</h1>
    </main>
  );
}
```

Save to: `apps/web/src/app/page.tsx`

- [ ] **Step 9: Install dependencies and type-check**

```bash
cd apps/web && npm install
npx tsc --noEmit
```

Expected: no TypeScript errors

- [ ] **Step 10: Commit**

```bash
git add apps/web/
git commit -m "feat: scaffold Next.js 14 web app with TypeScript and Tailwind"
```

---

## Task 11: Integration test — docker compose up

- [ ] **Step 1: Copy .env.example to .env and fill in values**

```bash
cp .env.example .env
```

Edit `.env` — set:
- `POSTGRES_PASSWORD=changeme_dev`
- `QDRANT_API_KEY=changeme_dev`
- `JWT_SECRET_KEY=` (run: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `ANTHROPIC_API_KEY=` (your real key, or a placeholder for now)

- [ ] **Step 2: Build and start all services**

```bash
docker compose up --build -d
```

Expected: all 6 containers start without error. Monitor with:
```bash
docker compose ps
```

Expected output: `api`, `web`, `postgres`, `redis`, `qdrant`, `celery_worker` all show `running` status.

- [ ] **Step 3: Run migrations inside the running API container**

```bash
docker compose exec api alembic upgrade head
```

Expected: `Running upgrade  -> 0001, initial_schema`

- [ ] **Step 4: Verify /health endpoint**

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"success": true, "data": {"status": "ok"}, "meta": {}}
```

- [ ] **Step 5: Verify web is served**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

Expected: `200`

- [ ] **Step 6: Verify Qdrant is reachable**

```bash
curl http://localhost:6333/healthz
```

Expected: `{"title":"qdrant - vector search engine"}`

- [ ] **Step 7: Tear down**

```bash
docker compose down
```

- [ ] **Step 8: Final commit**

```bash
git add .
git commit -m "chore: Phase 1 infrastructure complete — all services verified"
```

---

## Verification Checklist

Before calling Phase 1 done, confirm all of the following:

- [ ] `docker compose up --build` completes without errors
- [ ] `GET http://localhost:8000/health` returns `{"success": true, "data": {"status": "ok"}, "meta": {}}`
- [ ] `alembic upgrade head` creates all 7 tables
- [ ] `GET http://localhost:3000` returns 200
- [ ] `GET http://localhost:6333/healthz` returns Qdrant version info
- [ ] `cd apps/api && pytest tests/ -v` — all 9 tests pass
- [ ] `cd apps/web && npx tsc --noEmit` — no TypeScript errors
