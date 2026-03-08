# Phase 4 External Services Guide (AI Engine)

This guide covers operational setup for feature engineering, model scoring, and AI service deployment.

## Service Topology
- AI service runs as an internal FastAPI service on port `8001`
- API/worker call AI via `AI_SERVICE_URL`
- No public internet exposure for AI service

## Model Artifact Lifecycle
- Train models with `scripts/train_model.py`
- Store model/scaler artifacts in versioned object storage (S3 recommended)
- Promote model versions from staging to production with explicit tags

## Runtime Configuration
- `AI_SERVICE_URL` should target VPC-internal DNS
- Keep scorer process warm to preserve model cache
- Set request timeout at 3-5 seconds; alert on timeout spikes

## Performance Targets
- Cached scoring p95 < 20ms
- AI endpoint p95 < 100ms (including serialization)
- Error rate < 0.5%

## Monitoring
- Track:
  - Model load failures (`FileNotFoundError`)
  - Scoring latency
  - Confidence distribution drift over time
  - Direction distribution skew (BUY/SELL/HOLD)

## Safety Controls
- Reject scoring on malformed OHLCV payloads
- Keep fallback behavior in bot loop (skip signal on AI failure)
- Enforce minimum confidence threshold on bot configs

## Release Process
1. Train model on staging data
2. Validate backtest metrics and live paper metrics
3. Publish model artifacts
4. Deploy AI service revision
5. Smoke test `/health` and `/ai/signal`
