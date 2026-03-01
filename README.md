# Backend (Phase 1 - MT5 Connector)

## Included in this step
- `POST /mt5/connect-test` (MT5 credential validation)
- `PUT /mt5/account` (save encrypted MT5 account data)
- `GET /mt5/account/status` (connection config status)
- `PUT /trading/config` (save trading rules per user)
- `GET /trading/config` (read trading rules)
- `POST /bot/start` and `POST /bot/stop` (session control)
- `GET /bot/status` (bot runtime state)
- `POST /engine/tick` (tick ingestion and auto trade decisions)
- `POST /ai/evaluate` (standalone AI trade quality evaluation)
- `PUT /risk/config`, `GET /risk/config` (daily target/loss/capital controls)
- `PUT /session/config`, `GET /session/config` (session duration controls)
- `GET /summary?user_id=...` (balance/equity/margin + bot state)
- `GET /trades/open?user_id=...`, `GET /trades/closed?user_id=...` (open/closed trades)
- `GET /pnl/daily?user_id=...` (realized/unrealized/total PnL)
- `GET /notifications?user_id=...` (in-app/email notification feed)
- `POST /license/activate`, `GET /license/status` (user license activation/validation)
- `POST /admin/licenses`, `PUT /admin/licenses/{id}`, `POST /admin/licenses/{id}/revoke`, `GET /admin/licenses` (admin license management)
- `GET /metrics/latency` (p50/p95/p99 route and AI latency telemetry)
- SQLite persistence for MT5 accounts

## Run locally
1. Create environment and install:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Configure env:
   - `cp .env.example .env`
   - Set `APP_ENCRYPTION_KEY` (Fernet key) for persistent decryption
3. Start API:
   - `uvicorn app.main:app --reload`

## API Documentation (Swagger)
- Swagger UI: `http://127.0.0.1:8000/swagger`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Notes
- If the runtime cannot load the `MetaTrader5` package, `connect-test` returns `provider_unavailable`.
- `PUT /mt5/account` accepts `provider_unavailable` for development, but blocks on explicit `failed` validations.
- Trading engine rules implemented in step 4:
   - Entry by simple trend direction (`BUY` on uptick, `SELL` on downtick)
   - One open trade per user/symbol
   - Immediate close on profit/loss threshold
   - AI gate in `/engine/tick` now auto-evaluates each tick before entry
- AI filtering pipeline implemented in step 5:
   - Trend strength scoring
   - Volatility spike detection and blocking
   - News spike blocking (`news_spike=true`)
   - Confidence scoring + threshold rejection
   - Decision audit persistence in `ai_decisions`
- Risk/session controls implemented in step 6:
   - Daily profit target auto-stop
   - Daily loss limit auto-stop
   - Allocated capital enforcement before new entries
   - Session duration auto-stop on tick processing
   - Bot start requires trading + risk + session configs
- Mobile dashboard and alerts implemented in step 7:
   - Dashboard summary endpoint for balance/equity/margin
   - Open and closed trades endpoints
   - Daily PnL endpoint
   - In-app notifications emitted for trade open/close, profit target hit, loss limit hit, and bot stop
   - Optional email notifications supported by storage channel when enabled by caller
- Licensing/admin APIs implemented in step 8:
   - Backend license activation and status validation endpoints
   - Admin license creation, update, revoke, and listing
   - License event audit storage
   - Bot start now enforces valid active non-expired license
- NFR hardening implemented in step 9:
   - MT5 connect validation retry with exponential backoff + jitter
   - Idempotency support for `/engine/tick` via `Idempotency-Key` header
   - Latency metrics for AI and trade execution routes (`/metrics/latency`)
   - Graceful shutdown hook that stops running bot sessions
- This scaffold still does not include auth/RBAC.

## Deploy on Render

### Option A: Blueprint (`render.yaml`)
1. Push this repo to GitHub.
2. In Render, choose **New +** → **Blueprint**.
3. Select your repo and deploy.
4. Set environment variable `APP_ENCRYPTION_KEY` in the Render dashboard.

### Option B: Manual Web Service
If you create the web service manually in Render:
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`

### Required environment variables
- `APP_ENV=prod`
- `APP_ENCRYPTION_KEY=<fernet-key>`
- Optional: `DATABASE_PATH` (defaults to `./bot.db`)

### Important MT5 note for Render
- `MetaTrader5` is now installed only on Windows environments.
- On Render (Linux), MT5 validation returns `provider_unavailable`, while non-MT5 endpoints remain available.
# trading-bot-api
