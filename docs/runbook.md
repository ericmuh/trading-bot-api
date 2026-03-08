# Operations Runbook

## Deployment
- Build and push image through GitHub Actions deploy workflow.
- Deploy ECS task definition revision.
- Validate `/health` and websocket connectivity.

## Rollback
- Select previous ECS task definition revision.
- Force new deployment using previous image tag.
- Confirm traffic and metrics normalize.

## Database
- Run migrations via `alembic upgrade head`.
- Restore from RDS snapshots through AWS console.

## Incident Response
- Bot stuck in `starting`: reset state to `stopped`, clear `bot:stop:{id}`, retry start.
- MT5 session reconnect loops: clear `mt5:session:*` and `mt5:heartbeat:*` keys and restart worker.
- Redis pressure: inspect key sizes and expiration hygiene.
- DB connection exhaustion: check long transactions and scale pool/instance.

## Secret Rotation
- Rotate JWT keys in Secrets Manager.
- Deploy API/worker with new keys.
- Invalidate stale refresh sessions if required.

## Scaling
- Scale ECS desired count for API/worker.
- Increase RDS class during maintenance window.
- Scale Redis cluster when memory > 75% sustained.
