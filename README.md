# Finance Dashboard API

Backend for a finance dashboard: **users and roles**, **financial record CRUD** with filters, **aggregated dashboard endpoints**, **JWT authentication**, and **role-based access control**. Built with **FastAPI**, **SQLAlchemy 2**, and **SQLite** (file-based, zero external DB setup).

## How this maps to the assignment

| Requirement | Implementation |
|-------------|----------------|
| User & role management | `User` model with `Role` enum; admin-only `POST/PATCH /users`; `is_active` flag |
| Financial records | `FinancialRecord` with amount, type (income/expense), category, date, notes; full CRUD + filters |
| Dashboard summaries | `GET /dashboard/summary`, `/dashboard/trends`, `/dashboard/recent` |
| Access control | `require_roles(...)` dependency; permissions matrix below |
| Validation & errors | Pydantic schemas; `422` with `errors` body; consistent `401/403/404/409` |
| Persistence | SQLite (`finance_dashboard.db` by default) |

## Roles and permissions

| Capability | Viewer | Analyst | Admin |
|------------|--------|---------|-------|
| Dashboard (`/dashboard/*`) | Yes | Yes | Yes |
| List / get records | No | Yes | Yes |
| Create / update / delete records | No | No | Yes |
| Manage users (`/users`) | No | No | Yes |

**Viewer** is intentionally limited to **aggregates and recent activity**, not full record listing, to match “dashboard-only” access.

Inactive users receive **403** on login and on any authenticated route (after token issuance, deactivation is enforced on each request).

## Assumptions and tradeoffs

- **Global ledger**: Financial records are not scoped per user; any analyst/admin sees the same dataset. `created_by_id` is stored for audit only.
- **Soft delete**: `DELETE /records/{id}` sets `deleted_at`; deleted rows are excluded from reads and aggregates.
- **Auth**: JWT bearer tokens (not production-grade key rotation or refresh tokens).
- **Trends**: Computed in Python from filtered rows; fine for demos; for large datasets you would push bucketing into SQL.
- **Secrets**: Default `SECRET_KEY` in `app/config.py` must be overridden via env for anything beyond local dev.

## Setup

Python 3.11+ recommended.

```bash
cd PythonLTI
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Optional environment variables (see `app/config.py`):

- `DATABASE_URL` — default `sqlite:///./finance_dashboard.db`
- `SECRET_KEY` — JWT signing secret
- `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` — first-time seed (only when DB has zero users)

Run the server:

```bash
python main.py
# or: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- OpenAPI UI: `http://127.0.0.1:8000/docs`

On first startup, tables are created and a **seed admin** is inserted if the database is empty:

- Email: `admin@example.com`
- Password: `Admin12345!`

## API overview

### Auth

- `POST /auth/login` — JSON `{ "email", "password" }` → `{ "access_token", "token_type" }`

Send `Authorization: Bearer <token>` on protected routes.

### Users (admin)

- `GET /users` — list users  
- `POST /users` — create user (`email`, `password`, `full_name`, `role`)  
- `PATCH /users/{id}` — update `full_name`, `role`, `is_active` (at least one field required)

### Records (analyst: read; admin: write)

- `GET /records` — query params: `date_from`, `date_to`, `category`, `type` (`income` \| `expense`), `q` (search notes/category), `page`, `page_size`  
- `POST /records` — create (admin)  
- `GET /records/{id}` — detail (analyst, admin)  
- `PATCH /records/{id}` — partial update (admin)  
- `DELETE /records/{id}` — soft delete (admin)

### Dashboard (viewer, analyst, admin)

- `GET /dashboard/summary` — total income/expense, net balance, category breakdown, record count; optional `date_from`, `date_to`  
- `GET /dashboard/trends` — weekly or monthly buckets (`granularity=week|month`)  
- `GET /dashboard/recent` — latest entries by `created_at` (`limit` 1–50)

### Health

- `GET /health` — liveness check (no auth)

## Tests

```bash
pytest tests -q
```

Tests use a temporary SQLite file via `DATABASE_URL` set in `tests/conftest.py`.

## Project layout

- `app/main.py` — FastAPI app, lifespan, routers  
- `app/models.py` — SQLAlchemy models  
- `app/schemas.py` — Pydantic request/response models  
- `app/deps.py` — JWT extraction, `require_roles`  
- `app/services/` — user, record, and dashboard logic  
- `app/routers/` — HTTP layer  
- `tests/` — API and RBAC checks  
