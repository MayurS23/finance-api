from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.logger import logger, setup_logging
from app.routers import auth, dashboard, records, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    logger.info("Starting Finance Dashboard API", version=settings.APP_VERSION)

    # Create DB tables on startup (idempotent)
    await create_tables()
    logger.info("Database tables verified")

    yield

    logger.info("Finance Dashboard API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Finance Dashboard API

A backend for a multi-role finance dashboard with:

- **JWT authentication** (Bearer token)
- **Role-based access control** — `viewer`, `analyst`, `admin`
- **Financial records management** with filtering, pagination, and soft-delete
- **Dashboard analytics** — totals, category breakdowns, monthly trends

### Roles

| Role     | Records | Dashboard summary | User management |
|----------|---------|-------------------|-----------------|
| viewer   | Read    | Totals only       | Self only       |
| analyst  | Read    | Full summary      | Self only       |
| admin    | Full    | Full summary      | Full            |

### Quick Start

1. `POST /auth/register` — create your first account (auto-becomes admin)
2. `POST /auth/login` — get your Bearer token
3. Authorize using the 🔒 button above
""",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"], summary="Liveness check")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
