# Trading Platform Backend

Blueprint-driven backend scaffold aligned to Phase 1 (`P1.1` to `P1.6`).

## Phase 1 Status
- Project structure scaffolded (`app/api`, `app/core`, `app/domain`, `app/services`, `app/workers`, `app/trading`, `app/ai`)
- Async SQLAlchemy base and Alembic migration bootstrap added
- JWT auth service + endpoints added (`/api/v1/auth/*`)
- User profile endpoints added (`/api/v1/users/me`)
- Shared async Redis client + lock/pubsub helpers added
- Celery app, beat schedule, and task stubs added

## Run Local
1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env`
5. `uvicorn app.main:socket_app --reload`

If Redis is not running locally, keep `REDIS_REQUIRED=false` in `.env` and the API will still start (Redis-backed features will be disabled).

## Test
- `pytest app/tests -q`

## Build & Workers
- API docs: `http://127.0.0.1:8000/docs`
- Worker: `celery -A app.workers.celery_app:celery_app worker --loglevel=info -Q trading,admin,notifications`
- Beat: `celery -A app.workers.celery_app:celery_app beat --loglevel=info`

## External Services Guide
- See [docs/phase-1-external-services-guide.md](docs/phase-1-external-services-guide.md) for AWS, hosting, Redis/Postgres, secrets, and CI/CD setup.
