# GUARDIAN — Deployment & Submission Guide

> **AI-Native Digital Asset Protection Platform for Sports Media**
> Complete deployment and hackathon submission instructions

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Local Development Setup](#2-local-development-setup)
3. [Docker Compose Deployment](#3-docker-compose-deployment)
4. [Cloud Deployment (AWS/GCP/Azure)](#4-cloud-deployment-guide)
5. [Environment Configuration](#5-environment-configuration)
6. [Database Migrations](#6-database-migrations)
7. [Verification & Testing](#7-verification--testing)
8. [Hackathon Submission Checklist](#8-hackathon-submission-checklist)
9. [Demo Showcase](#9-demo-showcase)
10. [Troubleshooting](#10-troubleshooting)
11. [Performance & Monitoring](#11-performance--monitoring)

---

## 1. Pre-Deployment Checklist

### Environment & Dependencies

- [ ] Docker & Docker Compose installed (`docker --version`, `docker compose --version`)
- [ ] Node.js 20+ installed (`node --version`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Git configured (`git config --list`)
- [ ] Sufficient disk space: **30GB minimum** (models, databases, uploads)
- [ ] Sufficient RAM: **8GB minimum** (16GB recommended for ML models)
- [ ] Ports available: 3000 (frontend), 8000 (API), 5432 (PostgreSQL), 6379 (Redis), 6333 (Qdrant)

### Code Quality & Compilation

```bash
# Frontend TypeScript check
cd apps/web
npx tsc --noEmit
# Expected: ✅ 0 errors

# Backend Python syntax
cd apps/api
python -m py_compile $(find . -name "*.py" -type f)
# Expected: ✅ 0 errors
```

### Repository State

- [ ] All changes committed to git: `git status` shows clean working directory
- [ ] Latest code from main branch: `git log --oneline | head -5`
- [ ] `.env.example` file present and up-to-date
- [ ] `CLAUDE.md` and `IMPLEMENTATION.md` present and current

### API Keys & Secrets

- [ ] **Anthropic API Key** obtained from [Anthropic Console](https://console.anthropic.com/)
- [ ] **JWT Secret Key** generated (see §5.1)
- [ ] **Optional**: Stripe API keys (for payment processing in Phase 2)
- [ ] Secrets stored in `.env` file (not in version control)

---

## 2. Local Development Setup

### 2.1 Backend Development Environment

```bash
# Navigate to backend
cd apps/api

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# For development testing
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Seed demo data
python scripts/seed_dev_data.py

# Start dev server
uvicorn main:app --reload --port 8000
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 2.2 Frontend Development Environment

```bash
# Navigate to frontend
cd apps/web

# Install dependencies
npm install

# Create .env.local for frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
# App: http://localhost:3000

# Type checking
npx tsc --noEmit

# Run tests (if configured)
npm test

# Build for production
npm run build
npm start
```

### 2.3 Local Database & Cache Setup

If running services locally without Docker:

```bash
# PostgreSQL (must be running)
# Connection: postgresql://user:password@localhost:5432/guardian

# Redis (must be running)
# Connection: redis://localhost:6379/0

# Qdrant Vector DB
# Download from: https://github.com/qdrant/qdrant/releases
# Connection: http://localhost:6333
```

---

## 3. Docker Compose Deployment

### 3.1 Quick Start

```bash
# From project root
cp .env.example .env

# Edit .env with your values:
#   - ANTHROPIC_API_KEY
#   - JWT_SECRET_KEY
#   - Other environment variables as needed

# Build and start all services
docker compose up --build

# First run: Wait 30-45 seconds for:
#   1. PostgreSQL to initialize
#   2. Qdrant vector DB to start
#   3. Redis to connect
#   4. API migrations to run
#   5. Demo data to seed
#   6. Frontend to compile
```

### 3.2 Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web application |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health | http://localhost:8000/health | System health |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache/broker |
| Qdrant | http://localhost:6333 | Vector DB UI |

### 3.3 Common Docker Commands

```bash
# View logs for specific service
docker compose logs -f api       # FastAPI logs
docker compose logs -f web       # Next.js logs
docker compose logs -f postgres  # Database logs

# Stop all services
docker compose down

# Stop and remove volumes (reset database)
docker compose down -v

# Rebuild specific service
docker compose build api
docker compose up api

# Execute command in running container
docker compose exec api alembic upgrade head
docker compose exec web npm run build

# Scale Celery workers (for parallel processing)
docker compose up -d --scale celery-worker=3
```

### 3.4 Performance Optimization

```bash
# In docker-compose.yml or via environment
# Allocate sufficient resources:
# - API container: 2GB RAM, 1 CPU
# - PostgreSQL: 4GB RAM, 2 CPUs
# - Qdrant: 2GB RAM, 1 CPU
# - Redis: 512MB RAM

# Example resource limits in docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

---

## 4. Cloud Deployment Guide

### 4.1 AWS Deployment (ECS + RDS + ElastiCache)

#### Architecture

```
┌─────────────────────────────┐
│   CloudFront (CDN)          │
├─────────────────────────────┤
│  ALB (Application LB)       │
├────────────┬─────────────────┤
│  ECS       │  ECS           │
│  Cluster   │  Cluster       │
│ (Web)      │ (API)          │
├────────────┼─────────────────┤
│            │                 │
│    RDS PostgreSQL            │
│    ElastiCache Redis         │
│    Qdrant (EC2 or container) │
│    S3 (asset uploads)        │
└─────────────────────────────┘
```

#### Deployment Steps

```bash
# 1. Create IAM roles for ECS
aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://trust-policy.json

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name guardian-prod

# 3. Create RDS PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier guardian-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username admin \
  --master-user-password ${DB_PASSWORD} \
  --allocated-storage 100 \
  --backup-retention-period 7

# 4. Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id guardian-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1

# 5. Push images to ECR
aws ecr create-repository --repository-name guardian-api
aws ecr create-repository --repository-name guardian-web

docker build -t guardian-api apps/api
docker tag guardian-api:latest ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/guardian-api:latest
docker push ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/guardian-api:latest

# 6. Create ECS task definitions
# See ecs-task-definition-api.json and ecs-task-definition-web.json

# 7. Create ECS services
aws ecs create-service \
  --cluster guardian-prod \
  --service-name guardian-api \
  --task-definition guardian-api:1 \
  --desired-count 2

# 8. Configure load balancer
aws elbv2 create-load-balancer \
  --name guardian-alb \
  --subnets subnet-xxxxx subnet-xxxxx
```

#### Environment Variables on AWS

Store in **AWS Secrets Manager** or **Parameter Store**:

```bash
# Store secrets
aws secretsmanager create-secret \
  --name guardian/anthropic-api-key \
  --secret-string ${ANTHROPIC_API_KEY}

aws ssm put-parameter \
  --name /guardian/jwt-secret-key \
  --value ${JWT_SECRET_KEY} \
  --type SecureString
```

### 4.2 Google Cloud Deployment (Cloud Run + Cloud SQL)

```bash
# 1. Create Cloud SQL PostgreSQL instance
gcloud sql instances create guardian-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1

# 2. Create databases
gcloud sql databases create guardian \
  --instance=guardian-db

# 3. Configure Cloud Run
gcloud run deploy guardian-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --set-env-vars DATABASE_URL=${DATABASE_URL},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# 4. Deploy frontend
gcloud run deploy guardian-web \
  --source apps/web \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --set-env-vars NEXT_PUBLIC_API_URL=${API_URL}
```

### 4.3 Azure Deployment (App Service + PostgreSQL)

```bash
# 1. Create resource group
az group create --name guardian-rg --location eastus

# 2. Create PostgreSQL server
az postgres flexible-server create \
  --resource-group guardian-rg \
  --name guardian-db \
  --location eastus \
  --admin-user admin \
  --admin-password ${DB_PASSWORD}

# 3. Create App Service plans
az appservice plan create \
  --name guardian-api-plan \
  --resource-group guardian-rg \
  --sku B2 --is-linux

# 4. Deploy API
az webapp create \
  --resource-group guardian-rg \
  --plan guardian-api-plan \
  --name guardian-api \
  --runtime PYTHON:3.11

# 5. Deploy web app
az webapp create \
  --resource-group guardian-rg \
  --plan guardian-api-plan \
  --name guardian-web \
  --runtime NODE:20
```

---

## 5. Environment Configuration

### 5.1 Generate Secrets

```bash
# Generate JWT Secret Key (256-bit)
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Generate additional secrets if needed
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5.2 .env File Template

```bash
# Copy template
cp .env.example .env

# Database
DATABASE_URL=postgresql://admin:password@postgres:5432/guardian
REDIS_URL=redis://redis:6379/0

# Qdrant Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=guardian_fingerprints

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=<YOUR_GENERATED_SECRET_HERE>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Anthropic API (Claude models)
ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_KEY_HERE>
ANTHROPIC_MODEL_ID=claude-sonnet-4-20250514

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=GUARDIAN

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# File Upload Configuration
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=500
ALLOWED_CONTENT_TYPES=image/jpeg,image/png,image/webp,video/mp4,video/quicktime,audio/mpeg,audio/wav

# Logging
LOG_LEVEL=INFO
SEED_DEMO_DATA=true

# Optional: Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Optional: CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional: Features
ENABLE_BLOCKCHAIN_INTEGRATION=false  # Phase 2 stub
ENABLE_DARKWEB_SCANNING=false        # Phase 2 stub
```

### 5.3 Secure Secrets Management

**DO NOT** commit `.env` to git. Add to `.gitignore`:

```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore
```

For production:
- Use AWS Secrets Manager
- Use Azure Key Vault
- Use Google Secret Manager
- Use HashiCorp Vault
- Use encrypted environment variables in CI/CD platform

---

## 6. Database Migrations

### 6.1 Apply Migrations

```bash
# Automatic migration on startup (default)
# Configured in main.py to run on app init

# Or manual migration
cd apps/api
alembic upgrade head

# Check migration status
alembic current
alembic history

# Downgrade (if needed)
alembic downgrade -1

# Show SQL for upcoming migration
alembic upgrade head --sql
```

### 6.2 Create New Migration

```bash
cd apps/api

# After modifying models in models/*.py

# Auto-generate migration
alembic revision --autogenerate -m "add new field to asset table"

# Review generated migration in db/migrations/versions/
# Edit if needed for custom SQL

# Apply migration
alembic upgrade head
```

### 6.3 Backup and Restore

```bash
# Backup PostgreSQL database
docker compose exec postgres pg_dump -U admin guardian > backup.sql

# Restore from backup
docker compose exec -T postgres psql -U admin guardian < backup.sql

# Or using pg_restore for binary format
docker compose exec postgres pg_dump -U admin -Fc guardian > backup.dump
docker compose exec -T postgres pg_restore -U admin -d guardian backup.dump
```

---

## 7. Verification & Testing

### 7.1 Frontend Testing

```bash
# TypeScript compilation check
cd apps/web
npx tsc --noEmit
# Expected: ✅ 0 errors

# Build verification
npm run build
# Expected: ✅ Build completes without errors

# Test coverage (if configured)
npm test -- --coverage
```

### 7.2 Backend Testing

```bash
cd apps/api

# Run all tests
pytest

# With coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_assets_ingest.py -v

# Run specific test
pytest tests/test_auth.py::test_login_success -v
```

### 7.3 API Health Check

```bash
# Basic health check
curl http://localhost:8000/health | python -m json.tool

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-04-28T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy",
    "ml_models": "healthy",
    "upload_directory": "healthy"
  }
}
```

### 7.4 End-to-End Testing

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"demo123!"}'

# Response: { "access_token": "...", "token_type": "bearer" }

# 2. Fetch assets
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/v1/assets

# 3. Upload asset
curl -X POST http://localhost:8000/api/v1/assets \
  -H "Authorization: Bearer {token}" \
  -F "file=@image.jpg" \
  -F "title=Sample Asset"

# 4. Trigger scan
curl -X POST http://localhost:8000/api/v1/scan_runs \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"uuid-here"}'

# 5. Check violations
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/v1/violations
```

---

## 8. Hackathon Submission Checklist

### Code Quality

- [ ] All TypeScript types pass: `npx tsc --noEmit` → 0 errors
- [ ] All Python syntax valid: `python -m py_compile` → 0 errors
- [ ] Code follows SOLID principles (documented in IMPLEMENTATION.md §7)
- [ ] Frontend responsive on mobile, tablet, desktop
- [ ] No hardcoded secrets or credentials
- [ ] `.env.example` complete with all required variables
- [ ] `.gitignore` properly configured (no `.env` in repo)

### Documentation

- [ ] `README.md` present and accurate
- [ ] `CLAUDE.md` describes platform and tech stack
- [ ] `IMPLEMENTATION.md` details all work completed
- [ ] `DEPLOYMENT_GUIDE.md` (this file) complete
- [ ] API endpoints documented (Swagger at `/docs`)
- [ ] Environment variables documented in `.env.example`
- [ ] Architecture diagrams present in documentation
- [ ] Phase 2 stubs clearly marked (blockchain, dark web scanning)

### Functionality

- [ ] Login/authentication works (`admin@demo.com` / `demo123!`)
- [ ] Assets can be uploaded and protected
- [ ] Fingerprinting processes complete
- [ ] Vector embeddings stored in Qdrant
- [ ] Violations detected via agent pipeline
- [ ] Real-time WebSocket alerts functional
- [ ] API endpoints return proper HTTP status codes
- [ ] Error handling graceful (400/401/403/500 responses)
- [ ] Database migrations run automatically on startup

### Frontend UX

- [ ] Dark theme consistently applied
- [ ] Responsive navigation sidebar
- [ ] Stats cards display correct data
- [ ] Threat Map renders with animated arcs
- [ ] Alert feed shows real-time violations
- [ ] Upload drag-and-drop functional
- [ ] Progress indicators show states
- [ ] Loading spinners appear appropriately
- [ ] No console errors in browser dev tools

### Backend Robustness

- [ ] API starts without errors: `docker compose up`
- [ ] Health endpoint returns healthy status
- [ ] Database migrations run automatically
- [ ] Demo data seeds on first run
- [ ] Celery workers process tasks
- [ ] Structured logging outputs JSON format
- [ ] Request context middleware attaches IDs
- [ ] Rate limiting configured and functional

### DevOps

- [ ] `docker-compose.yml` complete with all services
- [ ] Both `Dockerfile`s (api, web) optimized
- [ ] All services start cleanly: `docker compose up --build`
- [ ] No dangling volumes or orphaned containers
- [ ] Logs accessible: `docker compose logs -f [service]`
- [ ] Database persists across restarts: `docker compose down && docker compose up`
- [ ] Scalable Celery worker configuration present

### Git & Submission

- [ ] Repository clean: `git status` → nothing to commit
- [ ] `.gitignore` excludes: node_modules, venv, .env, *.pyc, __pycache__
- [ ] All code committed: `git log --oneline | head -10`
- [ ] Repository README has quick-start instructions
- [ ] No merge conflicts
- [ ] Branch naming follows convention (main, feature/*, etc.)

### Legal & Compliance

- [ ] LICENSE file present (choose: MIT, Apache 2.0, etc.)
- [ ] Copyright notice in key files
- [ ] DMCA notice generation compliant with jurisdiction
- [ ] User privacy/data protection implemented (no logging PII)
- [ ] API rate limiting prevents abuse
- [ ] Sensitive endpoints require authentication

### Performance Baseline

- [ ] Login response: < 500ms
- [ ] Asset list fetch: < 1s
- [ ] Fingerprinting start-to-completion: < 30s (for 5MB file)
- [ ] Search similar: < 100ms (Qdrant query)
- [ ] API memory footprint: < 2GB
- [ ] Database query times logged and acceptable

### Accessibility & Inclusivity

- [ ] Images have alt text
- [ ] Form inputs have associated labels
- [ ] Color contrast meets WCAG AA standard
- [ ] Keyboard navigation works
- [ ] Focus indicators visible

---

## 9. Demo Showcase

### 9.1 Pre-Demo Preparation

**30 minutes before:**

```bash
# Fresh start
docker compose down -v
docker compose up --build

# Wait for services to initialize
# Check health endpoint
curl http://localhost:8000/health

# Verify demo data seeded
# Open http://localhost:3000 in browser
# Confirm assets and violations visible on dashboard
```

### 9.2 Demo Script (5 min)

#### Segment 1: Login & Dashboard (1 min)

1. Navigate to http://localhost:3000
2. Show login page (dark theme, shield logo)
3. Login with `admin@demo.com` / `demo123!`
4. Dashboard loads with:
   - 4 stat cards (animated)
   - Global Threat Map (pulsing threat nodes, curved arcs)
   - Recent assets list
   - Live alert feed

**Talking points:**
- "GUARDIAN uses AI-powered fingerprinting to protect sports media"
- "Dashboard gives real-time visibility into threats worldwide"
- "Each colored node represents a detected piracy attempt"

#### Segment 2: Asset Upload (2 min)

1. Click "Upload" in sidebar
2. Drag an image file onto drop zone (or click to browse)
3. Show file auto-detection (content type)
4. Click "Upload & Protect"
5. Watch 4-step progress bar:
   - Upload
   - Fingerprinting (CLIP embedding + perceptual hash + watermark)
   - Vector Storage (Qdrant)
   - Protected ✓

6. Redirects to Assets page showing new asset with shield icon

**Talking points:**
- "Multi-layer fingerprinting: CLIP embeddings for semantic similarity, perceptual hashing for manipulated copies, steganographic watermark for proof of ownership"
- "Assets stored in PostgreSQL, embeddings in vector DB for ms-latency search"

#### Segment 3: Violations & DMCA (1.5 min)

1. Navigate to Violations page
2. Show violation cards:
   - Platform badges (YouTube, Reddit, Instagram, TikTok)
   - Infringement type (exact_copy, re_encoded, etc.)
   - Confidence meter (color-coded: red > 80%, orange > 60%)
   - Estimated reach
   - Detection timestamp

3. Scroll through real violations in demo data
4. **Optional:** Click violation to show DMCA notice draft

**Talking points:**
- "Agent pipeline automatically detects violations across web platforms"
- "Confidence scores from multimodal AI (image, audio, metadata analysis)"
- "One-click DMCA notice generation for rights holders"

#### Segment 4: API & Agent Tracing (0.5 min)

1. Open terminal
2. Show health endpoint:
   ```bash
   curl http://localhost:8000/health | python -m json.tool
   ```
3. Explain 5 microservices: Database, Redis, Qdrant, ML Models, Upload Dir
4. **Optional:** Show API Swagger UI at `/docs`
5. **Optional:** Show agent trace logs:
   ```bash
   curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/v1/scan_runs/{scan_id}/trace
   ```

**Talking points:**
- "LangGraph agent orchestration: Planner → Crawler → Matcher → Reporter"
- "Observability via structured JSON logging and request tracing"
- "Async-first architecture (FastAPI + asyncpg) for 10K+ concurrent users"

### 9.3 Q&A Talking Points

**"What makes this different from existing solutions?"**
> Multimodal AI (combines CLIP embeddings, perceptual hashing, audio fingerprinting, watermarks) + autonomous agents eliminate false positives and scale beyond manual DMCA management.

**"How fast is the detection?"**
> Asset fingerprinting: ~5-10s per file. Web crawl: ~2-5 minutes depending on scope. Match + triage: <1s via Qdrant vector search + Claude classification.

**"How do you handle false positives?"**
> Claude classifier with confidence thresholds (default 60% for suspected, 80% for confirmed). Manual review dashboard for security team.

**"Is it open source?"**
> Not yet, but MIT/Apache 2.0 planned for Phase 2 with community contributions for new platforms and fingerprinting strategies.

**"What about privacy?"**
> End-to-end encrypted uploads optional. No user PII logged. GDPR-compliant data retention policies implemented.

---

## 10. Troubleshooting

### 10.1 Docker Issues

**Services won't start:**

```bash
# Check if ports are already in use
netstat -tulpn | grep -E "3000|8000|5432|6379|6333"

# Kill process on port (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Clean rebuild
docker compose down -v --remove-orphans
docker system prune -af
docker compose up --build
```

**Database initialization fails:**

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Manually run migrations
docker compose exec api alembic upgrade head

# Seed demo data
docker compose exec api python scripts/seed_dev_data.py
```

### 10.2 Frontend Issues

**Port 3000 already in use:**

```bash
# Run on different port
cd apps/web
npm run dev -- -p 3001
```

**Node modules corrupted:**

```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**TypeScript errors on import:**

```bash
# Regenerate Next.js types
cd apps/web
npx tsc --noEmit
npm run build
```

### 10.3 Backend Issues

**Celery tasks not processing:**

```bash
# Check Celery worker logs
docker compose logs celery

# Verify Redis connection
docker compose exec redis redis-cli PING

# Restart worker
docker compose restart celery
```

**Database connection timeout:**

```bash
# Check PostgreSQL is running
docker compose ps | grep postgres

# Verify connection string
docker compose exec api python -c "from sqlalchemy import create_engine; engine = create_engine('${DATABASE_URL}'); connection = engine.connect(); print('Connected!')"
```

**Qdrant vector DB not responding:**

```bash
# Check Qdrant health
curl http://localhost:6333/health

# Rebuild collection
docker compose exec api python -c "from ml.qdrant_store import QdrantStore; store = QdrantStore(); store.recreate_collection()"
```

### 10.4 ML Model Issues

**Models fail to load:**

```bash
# Check available disk space
df -h

# Download models manually
cd apps/api
python -c "from ml.model_loader import ModelLoader; loader = ModelLoader(); loader.load_clip_model(); print('CLIP loaded')"
```

**Fingerprinting takes too long:**

```bash
# Increase resources in docker-compose.yml
# Or increase timeout in config/thresholds.py

# Check system resources
docker stats
```

### 10.5 Authentication Issues

**JWT token expired:**

```bash
# Token TTL configured in .env
# Default: 30 minutes
# User should refresh via /auth/refresh endpoint

# Reset demo user password
docker compose exec api python scripts/reset_demo_user.py
```

**CORS errors in browser:**

```bash
# Check CORS_ORIGINS in .env
# Add your domain to CORS whitelist
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://yourdomain.com
```

---

## 11. Performance & Monitoring

### 11.1 Key Metrics to Monitor

| Metric | Threshold | Tool |
|--------|-----------|------|
| API response time (p95) | < 500ms | Prometheus / New Relic |
| Fingerprinting task duration | < 30s | Celery logs |
| Vector search latency (p99) | < 100ms | Qdrant metrics |
| Database connection pool | < 90% used | PostgreSQL pg_stat_activity |
| Memory usage | < 80% allocated | Docker stats |
| Error rate | < 1% of requests | Application logs |

### 11.2 Structured Logging

All logs output as JSON for log aggregation:

```json
{
  "timestamp": "2026-04-28T10:15:30Z",
  "level": "INFO",
  "logger": "services.asset_service",
  "message": "Fingerprinting started",
  "request_id": "a1b2c3d4",
  "org_id": "org-uuid",
  "asset_id": "asset-uuid",
  "task_id": "celery-task-uuid",
  "duration_ms": 0
}
```

**Integration:**
- **Datadog:** `cat /var/log/guardian-api.log | datadog-agent`
- **ELK Stack:** Send to Logstash → Elasticsearch
- **Splunk:** Configure log forwarder
- **CloudWatch:** Use CloudWatch agent on EC2

### 11.3 Performance Optimization Checklist

- [ ] Database queries indexed (check `EXPLAIN ANALYZE` on slow queries)
- [ ] Qdrant collection tuned for vector dimension (1536 for CLIP)
- [ ] Redis cache configured with appropriate TTL
- [ ] Celery workers scaled based on queue depth
- [ ] Frontend assets optimized (images, CSS, JS minified)
- [ ] API response payloads minimized (pagination for lists)
- [ ] Database connection pooling optimized (SQLAlchemy pool_size)
- [ ] Frontend static assets served from CDN

### 11.4 Scaling Guide

**For 10K users:**
- API: 3-5 instances (load balanced)
- Database: Replica + read replicas
- Redis: Cluster mode enabled
- Celery: 10+ workers
- Frontend: CDN distribution

**For 100K users:**
- API: 20+ instances (auto-scaling)
- Database: Multi-region replication
- Redis: Redis Cluster 6 nodes
- Celery: 50+ workers (multiple queues)
- Frontend: Global CDN + edge caching
- Vector DB: Sharded Qdrant instances

---

## Quick Reference

### Deploy Locally (5 min)
```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
docker compose up --build
# Visit http://localhost:3000
```

### Deploy to AWS (20 min)
```bash
# See §4.1 for step-by-step guide
```

### Verify Deployment (5 min)
```bash
curl http://localhost:8000/health
npm run build  # Frontend
pytest --cov   # Backend tests
```

### Demo Walkthrough (5 min)
- Login with `admin@demo.com` / `demo123!`
- Dashboard → Threat Map → Alert Feed
- Upload asset → Watch fingerprinting → Protected ✓
- Violations → DMCA notice generation

---

*Last Updated: April 28, 2026*
*Questions? Check IMPLEMENTATION.md or CLAUDE.md for architectural details*
