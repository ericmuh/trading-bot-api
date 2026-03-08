# Phase 1 External Services Guide (AWS, Hosting, Secrets)

This guide covers external systems for Phase 1 (`P1.1` to `P1.6`) so the backend is production-ready without hardcoded credentials.

## 1) AWS Accounts and Baseline

## Required
- 1 AWS account with least-privilege IAM users/roles
- 1 VPC with private subnets for data services
- 1 public subnet (or ALB-managed ingress)

## Recommended naming
- Environment prefixes: `dev`, `staging`, `prod`
- Service prefix: `trading-platform`

Example:
- `prod/trading-platform/api`
- `prod/trading-platform/worker`
- `prod/trading-platform/ai`

## 2) Secrets Management (AWS Secrets Manager)

Store all secrets in AWS Secrets Manager. Do not commit `.env` values beyond local development placeholders.

## Secret keys to create
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_PRIVATE_KEY`
- `JWT_PUBLIC_KEY`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `MT5_ENCRYPTION_KEY_ID`
- `AI_SERVICE_URL`

## Suggested secret path
- `/prod/trading-platform/backend`

## Retrieval pattern
- At container start, inject values as environment variables from Secrets Manager (ECS task definition secrets mapping).

## 3) Database Hosting

## Development
- Local SQLite is acceptable for Phase 1 local iteration.

## Staging/Production
- Use AWS RDS PostgreSQL 15+
- Enable automated backups (7–30 days)
- Enable Multi-AZ in production
- Restrict inbound rules to service security groups only

## Connection string format
- `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB_NAME`

## Migration flow
1. Build release image
2. Run Alembic migration job (`alembic upgrade head`)
3. Deploy API/worker

## 4) Redis Hosting

Use Redis for:
- Token revocation
- Locks
- Event pub/sub
- Celery broker/result backend

## Staging/Production
- AWS ElastiCache Redis 7+
- Enable AUTH/TLS where supported
- Use private subnets and SG restrictions

## Keyspace conventions
- `refresh:valid:{jti}`
- `lock:{resource}`
- `events:{channel}`

## 5) Hosting Options

## Option A (quick launch): Render
- Keep `backend/render.yaml` for non-critical environments
- Set all environment variables via dashboard secret settings

## Option B (recommended): AWS ECS Fargate
- Build images and push to ECR
- Run API and worker as separate ECS services
- Put API behind ALB
- Keep worker private (no public ingress)

## ECS services
- `trading-platform-api`
- `trading-platform-worker`
- `trading-platform-beat` (optional separate)

## 6) Celery Externalization

## Required runtime variables
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## Queue policy
- `trading` highest priority
- `admin` medium
- `notifications` lowest

## Operational checks
- Worker heartbeat in logs
- Beat emits scheduled tasks every 30/60 seconds and daily report schedule

## 7) TLS, Domains, and Edge Security

## Minimum
- HTTPS only
- Managed certificate (ACM if on AWS)
- WAF or equivalent edge filtering for API routes

## API route example
- `api.yourdomain.com` -> ALB -> FastAPI ECS service

## 8) Observability

## Logging
- Ship JSON logs to CloudWatch
- Include request path, status, latency, timestamp

## Alerts
- High 5xx rate
- API p95 latency breaches
- Worker queue backlog threshold
- Redis connection failures

## 9) CI/CD (GitHub Actions)

## Pipeline baseline
1. Lint + tests
2. Build image
3. Push to ECR
4. Run migrations
5. Deploy ECS service revision

## Branch strategy
- `main` -> production
- `develop` -> staging

## 10) Production Readiness Checklist (Phase 1)

- Secrets present in AWS Secrets Manager
- RDS + Redis reachable from API/worker SGs
- Alembic migration succeeds on target DB
- API health endpoint reachable over HTTPS
- Auth endpoints issue and validate JWT tokens
- User profile endpoints protected by auth middleware
- Redis lock and token revocation paths verified
- Celery worker and beat both running

## Next Phase

Phase 2 introduces MT5 account lifecycle and session pooling. Before starting:
- Confirm RDS and Redis are stable
- Confirm migration process is automated
- Confirm secrets rotation process is documented
