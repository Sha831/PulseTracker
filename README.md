# PulseTrack

PulseTrack is a backend event-ingestion and analytics API built with **FastAPI, PostgreSQL, SQLAlchemy, and Redis**. It accepts authenticated events from client applications, stores them in PostgreSQL, and exposes hourly analytics for each organization.

The project is being built as a **modular monolith** with a focus on backend fundamentals: API design, authentication, validation, transactional idempotency, scheduled aggregation, caching, and clear separation between API and service logic.

## Current Status

PulseTrack currently includes:

- Organization API-key authentication and JWT issuance.
- JWT verification and claim validation for protected endpoints.
- Validated, organization-scoped event ingestion.
- PostgreSQL persistence and database-backed idempotency.
- Hourly analytics aggregation into a separate analytics table.
- A scheduled aggregation job aligned to clock-hour boundaries.
- An analytics endpoint with time-range and optional event-type filtering.
- Redis caching for analytics responses, with a short TTL and a PostgreSQL fallback when Redis is unavailable.
- UTC normalization and validation for timezone-aware event and analytics timestamps.

Automated tests, Docker packaging, and deployment preparation are the next major phases. The project is still under development; those items should not be considered complete yet.

## Design Principles

- **Modular monolith:** one application with clearly separated modules, not a microservices system.
- **Stateless REST API:** JWTs authenticate protected requests.
- **Layered responsibilities:** API endpoints coordinate requests; service functions contain application logic; PostgreSQL remains the source of truth.
- **Organization isolation:** Analytics and event operations are scoped to the authenticated organization.
- **Database-backed idempotency:** Repeated requests with the same idempotency key should not create duplicate events.
- **Validated inputs:** Pydantic validates request data before business logic runs.
- **Cache as an optimization:** Redis improves repeated analytics reads but is not the source of truth.

## Features

### Authentication

- Organization API-key authentication at the token endpoint.
- JWT generation.
- JWT signature/expiry verification and claim validation.
- Protected endpoints using the authenticated organization identity.

### Event Ingestion

- REST endpoint for event ingestion.
- Pydantic request validation.
- Timezone-aware event timestamps normalized to UTC.
- Future-event and event-age validation.
- PostgreSQL persistence.
- Database-backed idempotency handling.

### Analytics

- Hourly aggregation of raw events into `hourly_event_analytics`.
- Scheduled aggregation using APScheduler.
- Analytics queries scoped to the authenticated organization.
- Optional event-type filtering.
- Hourly time buckets and bounded historical queries.
- UTC-aware range validation and exclusive upper-bound SQL filtering.

### Redis Cache

- Analytics responses cached in Redis.
- Cache keys include the organization, time range, and event-type filter.
- Cached responses use a TTL.
- Cache misses fall through to PostgreSQL.
- Redis read/write failures are designed not to make Redis a requirement for serving analytics.
- Invalid cached JSON can be treated as a cache miss and cleaned up.

## Architecture

```text
Client
  |
  v
FastAPI REST API
  |-- Authentication: API key -> JWT
  |-- Event ingestion
  |       |
  |       v
  |   PostgreSQL raw_events
  |
  |-- Analytics API
          |
          v
       Redis cache ---- cache hit ----> Response
          |
       cache miss / Redis failure
          |
          v
       PostgreSQL hourly_event_analytics
          ^
          |
Scheduled hourly aggregation job
          |
          v
       PostgreSQL raw_events
```

PostgreSQL is the source of truth. Redis is used only to accelerate analytics responses.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| API framework | FastAPI |
| Request/response validation | Pydantic |
| Database | PostgreSQL |
| Database access | SQLAlchemy |
| Authentication | JWT |
| Cache | Redis |
| Scheduled jobs | APScheduler |
| API documentation | Swagger UI / OpenAPI |
| Local Redis runtime | Docker |

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/token` | Authenticate an organization using its API key and issue a JWT |
| `POST` | `/events` | Ingest an event for the authenticated organization |
| `GET` | `/analytics` | Retrieve hourly analytics for a time range, optionally filtered by event type |

Interactive API documentation is available at `/docs` while the application is running.

Protected endpoints require a bearer token issued by `/auth/token`.

## Running Locally

### Prerequisites

- Python 3.13+
- `uv`
- PostgreSQL
- Redis
- Docker Desktop, if running Redis in a container

### 1. Get the project and install dependencies

```bash
git clone https://github.com/Sha831/PulseTracker.git
cd PulseTracker
cp .env.example .env
uv sync
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp` if needed.

### 2. Configure environment variables

Set the PostgreSQL connection URL, Redis URL, and required authentication/JWT settings in `.env`, following `.env.example`. Keep real secrets out of source control.

The application expects its configured PostgreSQL database and Redis service to be available before requests that depend on them are made.

### 3. Start Redis locally with Docker

If the project’s Redis container already exists, start it:

```powershell
docker start pulsetracker-redis
```

To check whether it is running:

```powershell
docker ps
```

If you have not created the container yet, create one with a password and a loopback-only port binding. Replace the placeholder with your own password:

```powershell
docker run --name pulsetracker-redis -p 127.0.0.1:6379:6379 -d redis redis-server --requirepass "YOUR_REDIS_PASSWORD"
```

Make sure the Redis URL in `.env` uses the same password. URL-encode special characters in the password when required.

### 4. Start the API

Ensure PostgreSQL is running, the database schema and required organization seed data are prepared, and `.env` is configured. Then run:

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the endpoints.

> The exact database initialization/seed workflow should follow the current project setup. A fully automated setup and migration workflow is part of the remaining project polish.

## Analytics Timestamp Behavior

- Analytics timestamps must be timezone-aware.
- Inputs are converted to UTC before hourly normalization.
- `from_` is normalized to the start of its hour.
- `to_` is normalized to its hour and then advanced by one hour to act as an exclusive SQL boundary.
- The SQL range is `bucket_start >= :from_ AND bucket_start < :to_`.
- Analytics are restricted to the configured 60-day lookback and completed-hour boundary.
- The `event_type` filter is optional; omitting it requests all event types.

## Roadmap

- [ ] Add automated tests for validation, authentication, event ingestion, idempotency, analytics, and caching.
- [ ] Test Redis failure and cache-corruption fallback behavior.
- [ ] Dockerize the FastAPI application and define a reproducible multi-service development setup.
- [ ] Review database migrations and startup/shutdown behavior.
- [ ] Improve logging and production configuration.
- [ ] Deploy the application and publish a demo.
- [ ] Finalize project documentation and examples.

## Project Goal

PulseTrack is a practical backend engineering project for demonstrating API development, authentication, data modeling, idempotency, scheduled processing, SQL analytics, caching, and operational readiness in a single modular application.

