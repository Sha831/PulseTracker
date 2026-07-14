# PULSETRACK


## Overview
PulseTrack is a backend event ingestion system built using RESTful API principles. It is designed to ingest events from client applications through authenticated REST APIs.

The project focuses on reliable event ingestion, idempotent request handling, stateless authentication using JWT.

PulseTrack is being developed to explore production-inspired backend architecture and will gradually evolve into a complete analytics platform.


## Design Principles
- Stateless REST APIs
- Layered architecture with clear separation of concerns
- Business logic isolated from the API layer
- Database-backed idempotency using transactions
- Request validation using Pydantic
- PostgreSQL as the source of truth
- Authentication before event processing


## Features
### ✅ Implemented
#### Authentication
- API Key authentication
- JWT generation
- JWT verification
- JWT claim validation

#### Event Ingestion
- REST API
- Request validation
- Idempotent event ingestion
- PostgreSQL persistence

### 🚧 In Progress
- Event aggregation
- Analytics endpoints
- Redis caching
- Background workers
- Kafka integration


## Tech Stack
| Layer          | Technology      |
| -------------- | --------------- |
|Language        |Python 3.13      |
| Framework      | FastAPI         |
| Validation     | Pydantic        |
| Database       | PostgreSQL      |
| ORM            | SQLAlchemy      |
| Authentication | JWT             |
| API Docs       | Swagger/OpenAPI |


## API Endpoints
| Method | Endpoint    | Purpose      |
| ------ | ----------- | ------------ |
| POST   | /auth/token | Generate JWT |
| POST   | /events     | Ingest Event |


## Folder Structure
```text
PulseTrack/
│
├── app/
│   ├── api/          # REST API endpoints
│   ├── auth/         # JWT and authentication logic
│   ├── db/           # Database configuration
│   ├── schemas/      # Pydantic models
│   ├── service/      # Business logic
│   ├── config.py     # Application configuration
│   └── main.py       # FastAPI entry point
│
├── .env.example
├── README.md
├── uv.lock
└── pyproject.toml
```


## Running Locally
### Prerequisites
- Python 3.13+
- uv
- PostgreSQL
```
git clone

cd PulseTrack

cp .env.example .env

uv sync

uv run uvicorn app.main:app --reload
```


## Roadmap
- Event aggregation
- Analytics endpoints
- Redis caching
- Background jobs
- Docker
- Testing
- CI/CD