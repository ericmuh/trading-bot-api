# Phase 2 External Services Guide (MT5 Integration)

This guide covers production handling for MT5 account connectivity (P2.1–P2.6).

## Required Secrets
- `MT5_ENCRYPTION_KEY` (base64-encoded 32-byte AES key)
- `MT5_LOGIN` (demo account for CI integration tests)
- `MT5_PASSWORD` (demo account password)
- `MT5_SERVER` (broker server name)

Store in AWS Secrets Manager and map to ECS task definitions.

## Redis Keys in Production
- Session registry: `mt5:session:{account_id}`
- Heartbeat: `mt5:heartbeat:{account_id}`
- Session lock: `mt5:session:lock:{account_id}`

## Redis Policy
- Enable TLS/auth in ElastiCache
- Set CloudWatch alarms on memory > 75%
- Set eviction policy to `volatile-ttl`

## MT5 Runtime Hosting
- MT5 Python package is Windows-native; Linux container support is limited.
- Recommended production pattern:
  - Run MT5 bridge workers on Windows hosts (self-managed or dedicated VM pool)
  - Keep API/Celery/control plane on Linux ECS
  - Use Redis as the cross-runtime coordination bus

## CI for Phase 2
- Add GitHub Action environment secrets:
  - `MT5_LOGIN`
  - `MT5_PASSWORD`
  - `MT5_SERVER`
  - `MT5_ENCRYPTION_KEY`
- Gate MT5 live tests behind an environment flag to avoid blocking every PR.

## Operational SLOs
- Session acquire p95 < 2s
- Heartbeat freshness < 30s for running sessions
- Reconnect success > 99% within 5 attempts

## Incident Runbook Snippets
- If duplicate sessions appear:
  1. Delete `mt5:session:lock:{account_id}`
  2. Delete stale `mt5:session:{account_id}`
  3. Re-issue bot start task

- If session loops in reconnect failures:
  1. Verify broker credentials and server reachability
  2. Rotate encrypted credentials with new MT5 password
  3. Confirm heartbeat keys are being refreshed
