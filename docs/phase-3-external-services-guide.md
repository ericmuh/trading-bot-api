# Phase 3 External Services Guide (Trading Engine)

This guide covers operations for strategy/risk/order/bot orchestration (P3.1–P3.7).

## Celery Queue Operations
- `trading` queue: bot start/stop and order workflows
- `admin` queue: heartbeat checks and account sync
- `notifications` queue: outbound user notifications

Recommended worker split:
- Worker group A: `trading` only
- Worker group B: `admin,notifications`

## Redis Production Keys
- Order idempotency: `trade:idem:{idempotency_key}`
- Order lock: `trade:lock:{account_id}:{symbol}`
- Bot heartbeat: `bot:heartbeat:{bot_id}`
- Bot stop signal: `bot:stop:{bot_id}`

## Scaling Guidance
- Start with 1 CPU per 20-30 active bots
- Keep average queue wait < 200ms for `trading`
- Increase worker concurrency in small increments (2 -> 4 -> 8)

## Risk and Safety Controls
- Enforce max drawdown and max trades at service layer
- Keep bot state machine transitions in DB transaction boundaries
- Alert if bot remains in `starting` > 120s

## Observability
- Track per-bot loop latency and order submission latency
- Track `RiskBreachError` by code (`MAX_DRAWDOWN`, `MAX_TRADES`, etc.)
- Track duplicate idempotency suppressions per symbol

## Incident Playbook
- Bot stuck in `starting`:
  1. Check `trading` queue backlog
  2. Check worker logs for runner startup errors
  3. Force state to `stopped` and restart via API

- Duplicate order concerns:
  1. Inspect idempotency keys for the time window
  2. Verify Redis expiration and lock contention
  3. Confirm client signal timestamp uniqueness
