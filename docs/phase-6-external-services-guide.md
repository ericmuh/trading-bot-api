# Phase 6 External Services Guide (Infrastructure & Production)

This guide covers production rollout controls for infrastructure phase tasks.

## AWS Core
- ECS Fargate services: `api`, `worker`, `beat`, `ai`
- RDS PostgreSQL Multi-AZ
- ElastiCache Redis replication group
- Secrets Manager for all credentials and keys

## Networking
- Place RDS/Redis in private subnets only
- Route public traffic via ALB + WAF to API service
- Keep AI service internal-only

## CI/CD
- `ci.yml` enforces lint/test/security and coverage gate
- `deploy.yml` publishes API image on `main`
- Add staged deployment + rollback pipeline step in production

## Monitoring
- API p95/p99 latency, 5xx rate
- Celery queue backlog and worker heartbeats
- MT5 session reconnect failure rate
- Redis memory and eviction metrics

## Security Baseline
- No plaintext secrets in repo or task definitions
- Rotate DB password and JWT keys on schedule
- Restrict IAM access by service role and environment
