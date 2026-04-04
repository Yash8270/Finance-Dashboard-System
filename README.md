# 💰 Finance Dashboard System - backend

A role-based REST API for managing financial records and serving dashboard analytics — built with **Python - FastAPI**, **SQLAlchemy 2.0**, and **TiDB Cloud** (MySQL-compatible).

> **Deployment status:** Database is live on **TiDB Cloud**. Backend is deployed on **Render** — https://finance-dashboard-system-qdw7.onrender.com/
>
> 🧪 **Want to interact with the API?** Visit the live interactive docs at **https://finance-dashboard-system-qdw7.onrender.com/docs** — no local setup needed.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | TiDB Cloud (MySQL-compatible) |
| Auth | JWT via `python-jose` + `bcrypt` |
| Validation | Pydantic v2 |
| Docs | Auto-generated Swagger UI (`/docs`) |

---

## 📁 Project Structure

```
├── main.py               # App entry point, middleware, router registration
├── db.py                 # DB engine, session factory, Base class
├── enums.py              # Shared enums — single source of truth for roles and types
├── database_setup.sql            # Raw SQL schema for manual database setup
├── models/
│   ├── user.py           # User ORM model
│   └── record.py         # Record ORM model (with soft delete + indexes)
├── schemas/
│   ├── user.py           # User request/response schemas with validation
│   └── record.py         # Record request/response schemas with validation
├── routes/
│   ├── auth.py           # POST /auth/register, POST /auth/login
│   ├── users.py          # User management (admin-gated)
│   ├── records.py        # Financial records CRUD
│   └── dashboard.py      # Aggregated summary endpoints
├── dependencies/
│   └── auth.py           # JWT guard + role-based guards (get_current_user, require_admin, etc.)
└── utils/
    └── auth.py           # Password hashing, token creation and decoding
```

The structure follows **separation of concerns**: routing → validation (schemas) → database (models), with auth logic isolated in `dependencies/` and `utils/`.

---

## ⚙️ Setup & Running Locally

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Create a `.env` file in the project root**
```env
HOST=your-tidb-host
DB_PORT=4000
DB_USER=your-db-user
PASSWORD=your-db-password
DATABASE=your-db-name
SECRET_KEY=any-long-random-string
```

> TiDB Cloud credentials can be found in your cluster's **Connect** panel. The connection uses SSL by default — no additional SSL config is required locally.

**3. Set up the database**

The app auto-creates tables on startup via SQLAlchemy. If you prefer to set up the schema manually, a raw SQL file is included:

```bash
mysql -h <host> -u <user> -p <database> < database_setup.sql
```

**4. Start the server**
```bash
uvicorn main:app --reload
```

**5. Open interactive API docs**
```
http://localhost:8000/docs
```

---

## 🗄️ Database Schema

Two tables — `users` and `records` — defined in [`database_setup.sql`](./database_setup.sql).

### `users`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `INT` | Primary key, auto-increment |
| `name` | `VARCHAR(100)` | Required |
| `email` | `VARCHAR(150)` | Unique, used as login identifier |
| `password` | `VARCHAR(255)` | bcrypt hash |
| `role` | `ENUM('admin', 'analyst', 'viewer')` | Defaults to `viewer` |
| `is_active` | `BOOLEAN` | Defaults to `true` |
| `created_at` | `DATETIME` | Auto-set on insert |

### `records`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `INT` | Primary key, auto-increment |
| `user_id` | `INT` | Foreign key → `users.id` |
| `amount` | `DOUBLE` | Must be greater than zero |
| `type` | `ENUM('income', 'expense')` | Required |
| `category` | `VARCHAR(100)` | Required, cannot be blank |
| `date` | `DATE` | Cannot be a future date |
| `notes` | `TEXT` | Optional |
| `created_at` | `DATETIME` | Auto-set on insert |

**Indexes on `records`:** `type`, `date`, `category`, `user_id` — covering the most common filter and dashboard query patterns.

**Foreign key:** `user_id` references `users.id` with `ON DELETE RESTRICT` (a user cannot be deleted while they have records) and `ON UPDATE CASCADE`.

---

## 🔐 Authentication Flow

This API uses **JWT Bearer tokens**. No sessions, no cookies.

1. `POST /auth/register` — create an account (role defaults to `viewer`)
2. `POST /auth/login` — receive a signed JWT (valid 24 hours)
3. Pass the token in the `Authorization: Bearer <token>` header on all protected routes
4. In Swagger UI, click **Authorize 🔒** and paste the token directly

---

## 👥 Role System & Access Control

Three roles with clearly enforced permission boundaries:

| Role | Dashboard | View Records | Create / Update / Delete Records | Manage Users |
|------|:---------:|:------------:|:---------------------------------:|:------------:|
| `viewer` | ✅ | ❌ | ❌ | ❌ |
| `analyst` | ✅ | ✅ | ❌ | ❌ |
| `admin` | ✅ | ✅ | ✅ | ✅ |

**How it's enforced:** Role guards (`require_admin`, `require_analyst_or_admin`) are FastAPI dependency functions injected directly into route signatures — no middleware magic, clearly visible at every route definition.

**Self-registration is always `viewer`** — the role field in the request body is ignored to prevent privilege escalation. Admins promote roles via `PATCH /users/{user_id}`.

---

## 📡 API Reference

### Auth
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/register` | Public | Register a new user account. Role is always set to `viewer` regardless of what is sent in the request body. |
| POST | `/auth/login` | Public | Authenticate with email and password. Returns a signed JWT valid for 24 hours. |

### Users
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/users/me` | All roles | Returns the profile of the currently authenticated user based on the JWT token. |
| GET | `/users` | Admin | Returns a list of all registered users in the system. |
| GET | `/users/{user_id}` | Admin | Returns the profile of a specific user by their ID. Returns `404` if not found. |
| PATCH | `/users/{user_id}` | Admin | Update a user's role (`viewer`, `analyst`, `admin`) or active status (`true`/`false`). At least one field must be provided. |

### Financial Records
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/records` | Analyst, Admin | Returns a paginated list of all active records. Supports filtering by `type`, `category`, `start_date`, and `end_date`. |
| GET | `/records/{record_id}` | Analyst, Admin | Returns a single financial record by ID. Returns `404` if the record doesn't exist or has been soft-deleted. |
| POST | `/records` | Admin | Create a new financial record. Amount must be greater than zero and date cannot be in the future. |
| PATCH | `/records/{record_id}` | Admin | Partially update an existing record — send only the fields you want to change. Empty body `{}` is rejected. |
| DELETE | `/records/{record_id}` | Admin | Soft-deletes the record by setting `is_deleted = true`. The record is hidden from all queries but preserved in the database for audit history. |

**Record filters (query params):** `type`, `category`, `start_date`, `end_date`, `skip`, `limit`

### Dashboard *(All authenticated roles)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Returns overall totals — total income, total expenses, and net balance across all active records. |
| GET | `/dashboard/categories` | Returns total amounts grouped by category and type, useful for pie or bar chart visualizations. |
| GET | `/dashboard/trends` | Returns monthly income and expense totals ordered chronologically, designed for line or area chart trend views. |
| GET | `/dashboard/recent` | Returns the most recent N active records as a lightweight summary. Default is 10, maximum is 100. |

---

## ✅ Validation & Error Handling

- **Pydantic v2** validates all request bodies — wrong types, missing fields, and constraint violations return `422` with clear messages
- `amount` must be `> 0`; `category` cannot be blank; `date` cannot be in the future
- `PATCH` endpoints reject empty bodies `{}` — at least one field must be present
- Password policy enforced at registration: min 8 chars, uppercase, lowercase, digit, special character
- A global exception handler catches unhandled 500 errors and returns a consistent JSON envelope instead of a raw traceback
- HTTP status codes used correctly: `201` on create, `204` on delete, `401`/`403`/`404` for access and not-found errors

---

## 🗑️ Soft Delete

Records are **never physically removed**. A `DELETE` request sets `is_deleted = true` — the row is preserved in the database for audit history but excluded from all read and write queries. This is enforced through a shared `_active_records()` base query used by every records route.

---

## 🔒 Security Notes

- Passwords hashed with **bcrypt** (constant-time comparison prevents timing attacks)
- Failed login returns the same error whether the email doesn't exist or the password is wrong — avoids leaking account existence
- `SECRET_KEY` is validated at startup — the server won't start without it (no insecure fallback)
- TiDB connections use SSL and connection pooling with `pool_pre_ping` to handle idle connection drops gracefully

---

## 📌 Assumptions & Tradeoffs

- **Records are global, not per-user.** All analysts/admins see all records. The `user_id` field tracks who created the record but does not scope visibility. This matches a shared finance dashboard where data is organizational, not personal.
- **Viewers see dashboard summaries but not raw records.** This supports an executive/read-only use case — high-level numbers without access to individual transactions.
- **Soft delete is intentional.** Financial records should not be permanently erased unilaterally. The `is_deleted` flag preserves audit history while keeping the API surface clean. A restore endpoint would be trivial to add.
- **No migrations tool used.** `create_all()` handles schema creation on startup. For a production system, Alembic would be the right choice.
- **Email is the unique login identifier.**
