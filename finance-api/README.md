<div align="center">

# Finance Dashboard API

### A production-ready backend for a multi-role financial management system

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_async-D71F00?style=for-the-badge&logoColor=white)](https://www.sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-40_Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

> Built with Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy (async) · JWT Auth · Docker

</div>

---

## What is this?

This is the complete backend for a **Finance Dashboard System** — a REST API that lets different types of users interact with financial data based on their role and permission level.

Think of it as the backend powering a tool like a company's internal finance tracker. A finance admin creates and manages transactions. An analyst reviews the data and generates insights. A viewer has read-only access to the dashboard numbers.

This project covers everything a real-world backend needs: authentication, authorization, data modeling, business logic, aggregated analytics, input validation, error handling, pagination, soft deletes, and a full test suite — all organized in a clean, maintainable structure.

---

## Why This Stack?

Every technology in this project was chosen deliberately.

**Python 3.12** — Strong typing via type hints, excellent async ecosystem, and the de-facto language for backend systems that need both speed and readability.

**FastAPI** — Built on top of Starlette and Pydantic. It gives you async request handling out of the box, automatic Swagger and ReDoc documentation, and a clean dependency injection system that makes auth and role guards trivially composable. It is the fastest Python framework in benchmarks and the cleanest in code.

**PostgreSQL 16** — The right database for financial data. It is relational, which means referential integrity (no orphaned records), ACID transactions (no partial writes), and powerful aggregation queries for dashboard analytics.

**SQLAlchemy 2.0 (async)** — The async ORM means database queries never block the event loop. SQLAlchemy 2.0 introduced a clean `select()` API that is fully type-safe. It keeps the database layer decoupled from business logic.

**Pydantic v2 + Pydantic Settings** — Request validation, response serialization, and environment config all use the same library. Pydantic v2 is 5–50x faster than v1 for validation. Every incoming request is validated against a schema before it ever touches the database.

**JWT (python-jose) + bcrypt** — Stateless authentication. Tokens are signed with a secret key and verified on every request without hitting the database. Passwords are hashed with bcrypt (cost factor 12), the industry standard for password storage.

**Structlog** — Structured JSON logging that makes logs machine-readable and easy to query in production log aggregators like Datadog or CloudWatch.

**Docker + Docker Compose** — One command to start the entire stack. No "it works on my machine" problems. PostgreSQL and the API server are wired together and ready to go.

**pytest + httpx AsyncClient** — Async test client that talks directly to the FastAPI app without starting a real server. Tests run against an in-memory SQLite database, so no external setup is needed.

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Tech Stack — Full Breakdown](#tech-stack--full-breakdown)
- [Role-Based Access Control](#role-based-access-control)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
  - [Option 1 — Docker (Recommended)](#option-1--docker-recommended)
  - [Option 2 — Manual Local Setup](#option-2--manual-local-setup)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Quick Start Walkthrough](#quick-start-walkthrough)
- [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
- [What Each File Does](#what-each-file-does)

---

## Features

- **JWT Authentication** — Secure login with Bearer tokens. Every protected endpoint verifies the token before processing.
- **Role-Based Access Control (RBAC)** — Three roles (`viewer`, `analyst`, `admin`) enforced at the dependency level. Not just checked in code — wired into the FastAPI dependency graph so it is impossible to skip.
- **Financial Records CRUD** — Create, read, update, and soft-delete financial transactions with full validation.
- **Filtering and Pagination** — Filter records by type, category, and date range. All list endpoints return paginated responses with total count and page metadata.
- **Dashboard Analytics** — Aggregated endpoints for total income, total expenses, net balance, category breakdowns, and monthly trends.
- **Soft Delete** — Records are never permanently deleted. Setting `is_deleted = true` hides them from all API responses while preserving them in the database for audit trails.
- **Input Validation** — Every request body and query parameter is validated by Pydantic before reaching business logic. Invalid input returns a structured 422 error, never a 500.
- **Structured Logging** — Every request and server event is logged as structured JSON using Structlog.
- **Auto-Generated API Docs** — Swagger UI at `/docs` and ReDoc at `/redoc` are generated automatically from the code. No separate documentation to maintain.
- **40 Tests** — Full coverage of auth, records CRUD, dashboard analytics, access control, and edge cases.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLIENT                                │
│          (Swagger UI / Postman / Frontend Application)          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │  HTTP + Bearer JWT
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Application                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │
│  │  /auth      │  │  /users     │  │  /records              │  │
│  │  register   │  │  CRUD       │  │  CRUD + filters        │  │
│  │  login      │  │  admin only │  │  pagination            │  │
│  └─────────────┘  └─────────────┘  └────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  /dashboard                                              │   │
│  │  /totals  /summary  /categories  /trends                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Dependency Layer                                        │   │
│  │  get_current_user  →  decode JWT  →  fetch user from DB  │   │
│  │  require_role      →  check hierarchy  →  allow or 403   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │  SQLAlchemy async (asyncpg)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                       PostgreSQL 16                             │
│                                                                 │
│   ┌──────────────────────┐    ┌────────────────────────────┐   │
│   │        users         │    │    financial_records       │   │
│   │──────────────────────│    │────────────────────────────│   │
│   │ id (PK)              │    │ id (PK)                    │   │
│   │ name                 │◄───│ created_by (FK→users.id)   │   │
│   │ email (unique index) │    │ amount                     │   │
│   │ password_hash        │    │ type  (income/expense)     │   │
│   │ role  (enum)         │    │ category  (indexed)        │   │
│   │ status (enum)        │    │ date  (indexed)            │   │
│   │ created_at           │    │ notes                      │   │
│   │ updated_at           │    │ is_deleted (soft delete)   │   │
│   └──────────────────────┘    │ created_at                 │   │
│                               │ updated_at                 │   │
│                               └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

Every request follows this exact sequence:

```
Request arrives
    │
    ▼
CORS Middleware
    │
    ▼
Router matches path and method
    │
    ▼
FastAPI resolves dependencies:
    1. HTTPBearer extracts token from Authorization header
    2. get_current_user decodes JWT → fetches user from DB → checks status
    3. require_role checks user.role against the required role level
    │
    ├── Auth fails       →  401 Unauthorized
    ├── Role too low     →  403 Forbidden
    │
    ▼
Pydantic validates request body and query params
    │
    ├── Validation fails →  422 Unprocessable Entity
    │
    ▼
Route handler executes business logic
    │
    ▼
SQLAlchemy executes async query against PostgreSQL
    │
    ▼
Pydantic serializes response model
    │
    ▼
JSON response returned to client
```

---

## Project Structure

```
finance-api/
│
├── app/                            Main application package
│   ├── __init__.py
│   ├── main.py                     FastAPI app creation, lifespan, router registration
│   ├── config.py                   All settings via Pydantic Settings (reads .env)
│   ├── database.py                 Async SQLAlchemy engine + get_db session dependency
│   ├── models.py                   ORM models: User, FinancialRecord + enums
│   ├── schemas.py                  Pydantic v2 request/response schemas + pagination
│   ├── auth.py                     bcrypt password hashing + JWT creation/verification
│   ├── dependencies.py             get_current_user, require_role factory, shorthands
│   ├── logger.py                   Structlog config (JSON in prod, pretty in dev)
│   │
│   └── routers/                    One file per domain area
│       ├── __init__.py
│       ├── auth.py                 POST /auth/login, POST /auth/register
│       ├── users.py                GET/POST/PATCH/DELETE /users
│       ├── records.py              GET/POST/PATCH/DELETE /records + filtering
│       └── dashboard.py            GET /dashboard/totals|summary|categories|trends
│
├── tests/                          Full test suite (40 tests)
│   ├── __init__.py
│   ├── conftest.py                 Fixtures: in-memory SQLite, async client, admin_client
│   ├── test_auth.py                9 tests: register, login, token validation
│   ├── test_records.py             16 tests: CRUD, filters, access control, edge cases
│   └── test_dashboard.py           15 tests: analytics, role enforcement, math correctness
│
├── .env.example                    Template — copy to .env and fill in values
├── .gitignore
├── Dockerfile                      Python 3.12-slim container for the API
├── docker-compose.yml              API + PostgreSQL wired together
├── pytest.ini                      asyncio_mode = auto, testpaths = tests
├── requirements.txt                All pinned dependencies
└── README.md                       This file
```

---

## Tech Stack — Full Breakdown

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| Language | Python | 3.12 | Type hints, async, rich ecosystem |
| Web Framework | FastAPI | 0.115.5 | Async, auto-docs, dependency injection |
| ASGI Server | Uvicorn | 0.32.1 | Production-grade async server |
| Database | PostgreSQL | 16 | Relational integrity, ACID, aggregations |
| ORM | SQLAlchemy | 2.0 async | Non-blocking queries, clean select() API |
| Async PG Driver | asyncpg | 0.30.0 | Fastest PostgreSQL driver for Python |
| DB Migrations | Alembic | 1.14.0 | Schema version control |
| Auth — JWT | python-jose | 3.3.0 | Sign and verify JWT tokens |
| Auth — Passwords | bcrypt | 4.2.1 | Industry-standard password hashing |
| Validation | Pydantic v2 | 2.10.2 | Request/response schemas, field validators |
| Config | Pydantic Settings | 2.6.1 | Type-safe env var loading from .env |
| Logging | Structlog | 24.4.0 | Structured JSON logs |
| Testing | pytest | 8.3.3 | Test runner |
| Test Client | httpx | 0.28.0 | Async HTTP client for FastAPI testing |
| Async Tests | pytest-asyncio | 0.24.0 | asyncio_mode = auto |
| Test DB | aiosqlite | — | In-memory SQLite (no real DB for tests) |
| Containers | Docker + Compose | Latest | Reproducible one-command setup |

---

## Role-Based Access Control

Three roles in a strict hierarchy. Higher roles inherit all permissions of lower roles.

```
viewer  (level 1)  →  read-only access to records and basic dashboard totals
analyst (level 2)  →  viewer + full dashboard: summary, categories, trends
admin   (level 3)  →  analyst + create/update/delete records + manage all users
```

### Permission Table

| Endpoint | viewer | analyst | admin |
|----------|:------:|:-------:|:-----:|
| `GET /records` | ✅ | ✅ | ✅ |
| `POST /records` | ❌ | ❌ | ✅ |
| `PATCH /records/:id` | ❌ | ❌ | ✅ |
| `DELETE /records/:id` | ❌ | ❌ | ✅ |
| `GET /dashboard/totals` | ✅ | ✅ | ✅ |
| `GET /dashboard/summary` | ❌ | ✅ | ✅ |
| `GET /dashboard/categories` | ❌ | ✅ | ✅ |
| `GET /dashboard/trends` | ❌ | ✅ | ✅ |
| `GET /users` | ❌ | ❌ | ✅ |
| `POST /users` | ❌ | ❌ | ✅ |
| `PATCH /users/:id` | ❌ | ❌ | ✅ |
| `DELETE /users/:id` | ❌ | ❌ | ✅ |
| `GET /users/me` | ✅ | ✅ | ✅ |

### How It Is Implemented

Role enforcement is not a manual `if` check inside each route. It is wired into FastAPI's dependency injection system, so it runs automatically before any route handler executes and cannot be forgotten.

```python
# dependencies.py

_ROLE_LEVEL = {Role.viewer: 1, Role.analyst: 2, Role.admin: 3}

def require_role(*roles: Role):
    min_level = min(_ROLE_LEVEL[r] for r in roles)

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if _ROLE_LEVEL[current_user.role] < min_level:
            raise HTTPException(403, "Access denied")
        return current_user

    return _check

# In any router — one line to protect an endpoint
@router.post("/records", dependencies=[Depends(require_admin)])
```

---

## API Reference

### Authentication

| Method | Endpoint | Auth Required | Description |
|--------|----------|:-------------:|-------------|
| `POST` | `/auth/register` | No | Register a new user. The very first user automatically becomes admin. |
| `POST` | `/auth/login` | No | Authenticate and receive a JWT access token. |

**Register — Request Body**
```json
{
  "name": "Mayur S",
  "email": "mayur@example.com",
  "password": "securepassword",
  "role": "viewer"
}
```

**Login — Request Body**
```json
{
  "email": "mayur@example.com",
  "password": "securepassword"
}
```

**Login — Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "3f7a2b1c-...",
    "name": "Mayur S",
    "email": "mayur@example.com",
    "role": "admin",
    "status": "active",
    "created_at": "2024-03-01T10:00:00Z",
    "updated_at": "2024-03-01T10:00:00Z"
  }
}
```

---

### Users *(admin only, except `/me`)*

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users` | admin | List all users (paginated) |
| `POST` | `/users` | admin | Create a user with a specific role |
| `GET` | `/users/me` | any | Get your own profile |
| `GET` | `/users/{id}` | admin | Get any user by ID |
| `PATCH` | `/users/{id}` | admin | Update name, role, or status |
| `DELETE` | `/users/{id}` | admin | Delete a user (cannot delete yourself) |

---

### Financial Records

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/records` | viewer+ | List records with optional filters and pagination |
| `POST` | `/records` | admin | Create a financial record |
| `GET` | `/records/{id}` | viewer+ | Get a specific record |
| `PATCH` | `/records/{id}` | admin | Update a record |
| `DELETE` | `/records/{id}` | admin | Soft-delete a record |

**Query Parameters for `GET /records`**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `type` | `income` \| `expense` | Filter by transaction type | `?type=expense` |
| `category` | string | Partial match on category | `?category=rent` |
| `date_from` | `YYYY-MM-DD` | Start of date range (inclusive) | `?date_from=2024-01-01` |
| `date_to` | `YYYY-MM-DD` | End of date range (inclusive) | `?date_to=2024-03-31` |
| `page` | int ≥ 1 | Page number | `?page=2` |
| `page_size` | int 1–100 | Results per page | `?page_size=50` |

**Create Record — Request Body**
```json
{
  "amount": 5000.00,
  "type": "income",
  "category": "Salary",
  "date": "2024-03-01",
  "notes": "March salary"
}
```

**Paginated Response Format**
```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

### Dashboard Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/dashboard/totals` | viewer+ | Total income, expenses, net balance |
| `GET` | `/dashboard/summary` | analyst+ | Full summary with categories, trends, recent activity |
| `GET` | `/dashboard/categories` | analyst+ | Per-category totals, optionally filtered by `type` |
| `GET` | `/dashboard/trends` | analyst+ | Monthly trends — pass `?months=N` (default 12, max 24) |

**`GET /dashboard/totals` — Response**
```json
{
  "total_income": 45000.00,
  "total_expenses": 18500.00,
  "net_balance": 26500.00
}
```

**`GET /dashboard/summary` — Response**
```json
{
  "total_income": 45000.00,
  "total_expenses": 18500.00,
  "net_balance": 26500.00,
  "record_count": 87,
  "category_totals": [
    { "category": "Salary",    "total": 40000.00, "count": 4 },
    { "category": "Freelance", "total": 5000.00,  "count": 2 },
    { "category": "Rent",      "total": 12000.00, "count": 4 }
  ],
  "monthly_trends": [
    { "month": "2024-03", "income": 10000.00, "expense": 4500.00, "net": 5500.00 },
    { "month": "2024-02", "income": 8500.00,  "expense": 3800.00, "net": 4700.00 }
  ],
  "recent_activity": [...]
}
```

---

### System

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | None | Liveness check |
| `GET` | `/docs` | None | Swagger UI |
| `GET` | `/redoc` | None | ReDoc API documentation |

---

## Data Models

### User

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Auto-generated PK |
| `name` | VARCHAR(100) | Display name |
| `email` | VARCHAR(255) | Unique, indexed, stored lowercase |
| `password_hash` | VARCHAR(255) | bcrypt hash — plain text is never stored |
| `role` | ENUM | `viewer`, `analyst`, or `admin` |
| `status` | ENUM | `active` or `inactive` — inactive users cannot log in |
| `created_at` | TIMESTAMPTZ | Set on insert |
| `updated_at` | TIMESTAMPTZ | Updated automatically on change |

### FinancialRecord

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID string | Auto-generated PK |
| `amount` | FLOAT | Always positive — type field determines income vs expense |
| `type` | ENUM | `income` or `expense` |
| `category` | VARCHAR(50) | User-defined label, indexed for filtering |
| `date` | VARCHAR(10) | `YYYY-MM-DD` format, indexed for date range queries |
| `notes` | TEXT | Optional description, nullable |
| `is_deleted` | BOOLEAN | Soft delete flag, default false |
| `created_by` | VARCHAR | FK → users.id |
| `created_at` | TIMESTAMPTZ | Set on insert |
| `updated_at` | TIMESTAMPTZ | Updated automatically on change |

---

## Prerequisites

### For Docker Setup *(Recommended)*

**Docker Desktop** — [Download here](https://www.docker.com/products/docker-desktop/)

Includes both Docker Engine and Docker Compose. Available for macOS, Windows, and Linux.

```bash
docker --version          # Docker version 24.x or higher
docker compose version    # Docker Compose version v2.x or higher
```

---

### For Manual Local Setup

**Python 3.12+** — [Download here](https://www.python.org/downloads/)

```bash
python --version    # Python 3.12.x
```

**PostgreSQL 16+** — [Download here](https://www.postgresql.org/download/)

```bash
# macOS (Homebrew)
brew install postgresql@16

# Ubuntu / Debian
sudo apt install postgresql-16

# Verify
psql --version    # psql (PostgreSQL) 16.x
```

**pip** — comes bundled with Python

```bash
pip --version
```

---

## Installation and Setup

### Option 1 — Docker (Recommended)

Docker starts both PostgreSQL and the API server automatically with a single command. No manual database setup is required.

**Step 1 — Clone the repository**

```bash
git clone https://github.com/MayurS23/finance-api.git
cd finance-api
```

**Step 2 — Configure environment variables**

```bash
cp .env.example .env
```

The default values work with Docker out of the box. For a production deployment, generate a strong secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the value of `SECRET_KEY` in your `.env` file.

**Step 3 — Start the full stack**

```bash
docker compose up --build
```

This will:
1. Pull the official PostgreSQL 16 Docker image
2. Build the FastAPI application container from the `Dockerfile`
3. Start PostgreSQL on port `5432`
4. Wait for PostgreSQL to pass its health check
5. Start the API server on port `8000` with `--reload`

Expected output:

```
finance-api-postgres-1  | database system is ready to accept connections
finance-api-api-1       | INFO  Starting Finance Dashboard API version=1.0.0
finance-api-api-1       | INFO  Database tables verified
finance-api-api-1       | INFO  Application startup complete.
finance-api-api-1       | INFO  Uvicorn running on http://0.0.0.0:8000
```

**Step 4 — Verify**

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}
```

**Step 5 — Open the interactive API docs**

Visit **http://localhost:8000/docs** in your browser. Swagger UI lets you test every endpoint directly.

**To stop:**
```bash
docker compose down
```

**To stop and wipe all data:**
```bash
docker compose down -v
```

---

### Option 2 — Manual Local Setup

**Step 1 — Clone the repository**

```bash
git clone https://github.com/MayurS23/finance-api.git
cd finance-api
```

**Step 2 — Create and activate a virtual environment**

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt after activation.

**Step 3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4 — Set up the database**

Make sure PostgreSQL is running, then create the database:

```bash
psql -U postgres -c "CREATE DATABASE finance_db;"
```

**Step 5 — Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and update `DATABASE_URL` with your local credentials:

```
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/finance_db
SECRET_KEY=your-generated-secret-key
```

**Step 6 — Start the server**

```bash
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on the first startup. Open **http://localhost:8000/docs** to explore the API.

---

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/finance_db` | Yes | Async PostgreSQL connection string. Must use the `asyncpg` prefix. |
| `SECRET_KEY` | `finance-dev-secret-...` | **Yes in production** | JWT signing key. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` | No | JWT algorithm. HS256 is standard for symmetric signing. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | No | Token lifetime in minutes. Default is 24 hours. |
| `DEBUG` | `false` | No | Enables SQL echo and pretty-printed logs. Never use `true` in production. |
| `DEFAULT_PAGE_SIZE` | `20` | No | Default results per page on list endpoints. |
| `MAX_PAGE_SIZE` | `100` | No | Maximum page size a client can request. |

> **Never commit your `.env` file to version control.** It is already excluded by `.gitignore`. In production, inject these as environment variables directly rather than using a file.

---

## Running Tests

The test suite does not need PostgreSQL. It overrides the database dependency with an in-memory SQLite database that is created fresh for each test session and destroyed automatically when the tests finish.

**Run all 40 tests:**

```bash
pytest tests/ -v
```

**Run a specific file:**

```bash
pytest tests/test_auth.py -v
pytest tests/test_records.py -v
pytest tests/test_dashboard.py -v
```

**Run a single test:**

```bash
pytest tests/test_records.py::test_admin_can_soft_delete_record -v
```

**Expected output:**

```
tests/test_auth.py::test_register_first_user_becomes_admin            PASSED
tests/test_auth.py::test_register_duplicate_email_returns_409         PASSED
tests/test_auth.py::test_register_short_password_returns_422          PASSED
tests/test_auth.py::test_login_success                                PASSED
tests/test_auth.py::test_login_wrong_password_returns_401             PASSED
tests/test_auth.py::test_login_nonexistent_email_returns_401          PASSED
tests/test_auth.py::test_protected_route_without_token_returns_401    PASSED
tests/test_auth.py::test_protected_route_with_invalid_token_returns_401 PASSED
tests/test_auth.py::test_get_me_returns_current_user                  PASSED
tests/test_dashboard.py::test_totals_accessible_by_viewer             PASSED
tests/test_dashboard.py::test_totals_correct_values                   PASSED
tests/test_dashboard.py::test_summary_requires_analyst_role           PASSED
tests/test_dashboard.py::test_summary_accessible_by_admin             PASSED
tests/test_dashboard.py::test_summary_structure                       PASSED
tests/test_dashboard.py::test_summary_net_balance_equals_income_minus_expenses PASSED
tests/test_dashboard.py::test_recent_activity_max_10_items            PASSED
tests/test_dashboard.py::test_categories_returns_list                 PASSED
tests/test_dashboard.py::test_categories_filter_by_type               PASSED
tests/test_dashboard.py::test_categories_sorted_by_total_descending   PASSED
tests/test_dashboard.py::test_trends_returns_list                     PASSED
tests/test_dashboard.py::test_trends_months_param                     PASSED
tests/test_dashboard.py::test_trends_invalid_months_returns_422       PASSED
tests/test_dashboard.py::test_trends_net_equals_income_minus_expense  PASSED
tests/test_dashboard.py::test_health_endpoint                         PASSED
tests/test_records.py::test_admin_can_create_record                   PASSED
tests/test_records.py::test_create_record_negative_amount_returns_422 PASSED
tests/test_records.py::test_create_record_invalid_date_returns_422    PASSED
tests/test_records.py::test_create_record_invalid_type_returns_422    PASSED
tests/test_records.py::test_viewer_cannot_create_record               PASSED
tests/test_records.py::test_list_records_returns_paginated            PASSED
tests/test_records.py::test_get_record_by_id                          PASSED
tests/test_records.py::test_get_nonexistent_record_returns_404        PASSED
tests/test_records.py::test_filter_by_type                            PASSED
tests/test_records.py::test_filter_by_date_range                      PASSED
tests/test_records.py::test_filter_by_category                        PASSED
tests/test_records.py::test_admin_can_update_record                   PASSED
tests/test_records.py::test_update_with_no_fields_returns_400         PASSED
tests/test_records.py::test_update_nonexistent_record_returns_404     PASSED
tests/test_records.py::test_admin_can_soft_delete_record              PASSED
tests/test_records.py::test_delete_nonexistent_record_returns_404     PASSED

40 passed in 14.38s
```

---

## Quick Start Walkthrough

Once the server is running, here is the complete flow from zero to live dashboard data.

**1. Register your first account — it automatically becomes admin**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mayur S",
    "email": "mayur@example.com",
    "password": "securepassword123",
    "role": "admin"
  }'
```

**2. Log in and save your token**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mayur@example.com",
    "password": "securepassword123"
  }'
```

Copy the `access_token` value from the response. Set it as a shell variable for convenience:

```bash
export TOKEN="paste_your_token_here"
```

**3. Create financial records**

```bash
# Add income
curl -X POST http://localhost:8000/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "type": "income", "category": "Salary", "date": "2024-03-01"}'

# Add an expense
curl -X POST http://localhost:8000/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1200, "type": "expense", "category": "Rent", "date": "2024-03-05"}'

# Add another expense
curl -X POST http://localhost:8000/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 300, "type": "expense", "category": "Groceries", "date": "2024-03-10"}'
```

**4. Filter records**

```bash
# Only expenses
curl "http://localhost:8000/records?type=expense" \
  -H "Authorization: Bearer $TOKEN"

# Specific date range
curl "http://localhost:8000/records?date_from=2024-03-01&date_to=2024-03-31" \
  -H "Authorization: Bearer $TOKEN"

# Category search (partial match)
curl "http://localhost:8000/records?category=Sal" \
  -H "Authorization: Bearer $TOKEN"
```

**5. View the dashboard**

```bash
# Quick balance (available to all roles)
curl http://localhost:8000/dashboard/totals \
  -H "Authorization: Bearer $TOKEN"

# Full analytics (analyst+ only)
curl http://localhost:8000/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"

# Monthly trends for the last 6 months
curl "http://localhost:8000/dashboard/trends?months=6" \
  -H "Authorization: Bearer $TOKEN"
```

**6. Test RBAC — create a viewer and confirm they cannot write**

```bash
# Create a viewer
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Finance Viewer",
    "email": "viewer@example.com",
    "password": "viewerpassword",
    "role": "viewer"
  }'

# Log in as the viewer
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "viewer@example.com", "password": "viewerpassword"}'

export VIEWER_TOKEN="paste_viewer_token_here"

# Attempt to create a record — returns 403 Forbidden
curl -X POST http://localhost:8000/records \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "type": "expense", "category": "Test", "date": "2024-03-01"}'

# But reading records works fine
curl http://localhost:8000/records \
  -H "Authorization: Bearer $VIEWER_TOKEN"
```

---

## What Each File Does

| File | Responsibility |
|------|----------------|
| `app/main.py` | Creates the FastAPI instance, registers all routers, sets up CORS middleware, and runs `create_tables()` on startup. |
| `app/config.py` | Single source of truth for all configurable values. Pydantic Settings reads from `.env` automatically and validates types at startup. |
| `app/database.py` | Creates the async SQLAlchemy engine with connection pooling. Defines `get_db()` — the FastAPI dependency that provides a session per request and handles commit/rollback. |
| `app/models.py` | SQLAlchemy ORM models (`User`, `FinancialRecord`) and Python enums (`Role`, `UserStatus`, `TransactionType`). Column types, constraints, indexes, and relationships are all here. |
| `app/schemas.py` | Pydantic v2 schemas for every request body and response shape. Completely separate from ORM models. FastAPI uses these to validate input and serialize output. |
| `app/auth.py` | `hash_password` and `verify_password` using bcrypt directly. `create_access_token` and `decode_access_token` using python-jose. No database access. |
| `app/dependencies.py` | `get_current_user` extracts the token, decodes it, and fetches the user from the database. `require_role` is a factory function that returns a role-checking dependency for any route. |
| `app/logger.py` | Configures Structlog. Pretty-printed in debug mode, structured JSON in production. |
| `app/routers/auth.py` | Register and login endpoints. The first registered user is automatically promoted to admin. |
| `app/routers/users.py` | Full user management. All endpoints except `GET /users/me` require admin. Prevents admins from deleting or demoting themselves. |
| `app/routers/records.py` | Full record management. List supports filtering and pagination. Delete is soft only. |
| `app/routers/dashboard.py` | Four analytics endpoints. Aggregations over the full record set, with role enforcement per endpoint. |
| `tests/conftest.py` | Sets `DATABASE_URL` to in-memory SQLite before any imports. Builds the test table schema once. Provides `client` and `admin_client` fixtures used across all tests. |
| `tests/test_auth.py` | 9 tests: registration, login, first-user-becomes-admin logic, bad credentials, invalid tokens, unauthenticated access. |
| `tests/test_records.py` | 16 tests: full CRUD, all filter types, pagination structure, soft-delete behavior, viewer RBAC enforcement. |
| `tests/test_dashboard.py` | 15 tests: response shapes, math correctness (net = income − expense), role restrictions, parameter validation. |

---

## Design Decisions and Trade-offs

**JWT over sessions** — JWT tokens are stateless. The server does not store session data, which means the API scales horizontally with no shared state store. The trade-off is that tokens cannot be invalidated before they expire. For a dashboard system with 24-hour tokens, this is acceptable. A system requiring instant revocation would add a Redis token blacklist.

**Soft delete** — Permanently deleting financial records destroys the audit trail. Soft delete sets `is_deleted = true` and hides the record from all responses while keeping it in the database. Any query that touches records includes a `WHERE is_deleted = false` filter, handled centrally in the route helpers.

**First user auto-promoted to admin** — A fresh deployment has no users and no admin to create other admins. Making the first registered user an admin is the standard bootstrap pattern. It is documented behavior, not a backdoor.

**`create_tables()` on startup vs Alembic** — `create_tables()` calls `Base.metadata.create_all()`, which is idempotent and safe to run repeatedly. It is convenient for development. For production, remove this call and run `alembic upgrade head` in the deployment pipeline. The models are fully Alembic-compatible — scaffold with `alembic init alembic`.

**Python aggregations vs SQL GROUP BY** — Dashboard analytics aggregate in Python for clarity. The code is easy to read and test. For datasets up to tens of thousands of records this is fast. For larger scale, push the aggregations down to SQL `GROUP BY` queries with proper indexes.

| Decision | Gain | Trade-off |
|----------|------|-----------|
| JWT (stateless) | Horizontal scalability | Cannot revoke tokens before expiry |
| Soft delete | Full audit trail | Every query needs `is_deleted = false` filter |
| First user = admin | Zero-config bootstrap | Must be documented (it is) |
| `create_tables()` | Instant dev setup | Not suitable for production schema changes |
| Python aggregations | Readable and testable | Less efficient at very large scale |

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

Built by [Mayur S](https://github.com/MayurS23)

</div>
