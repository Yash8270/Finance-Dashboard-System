from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from db import engine, Base

# Import all models so SQLAlchemy registers them before create_all
import models.user   
import models.record  

from routes import auth, users, records, dashboard

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Dashboard API",
    description="""
## Finance Dashboard — Role-Based REST API

A clean JWT-authenticated REST API with Role-Based Access Control (RBAC),
built with FastAPI, SQLAlchemy, and TiDB Cloud (MySQL-compatible).

---

### How to Authenticate in Swagger

1. Call **POST /auth/login** with your email and password
2. Copy the `access_token` from the response
3. Click the **Authorize** button at the top
4. Paste your token in the value field
5. Click **Authorize** — all protected routes are now unlocked

---

### Role Permissions

| Role      | Dashboard | View Records | Create / Update / Delete Records | Manage Users |
|-----------|:---------:|:------------:|:--------------------------------:|:------------:|
| `viewer`  | Yes       | No           | No                               | No           |
| `analyst` | Yes       | Yes          | No                               | No           |
| `admin`   | Yes       | Yes          | Yes                              | Yes          |

All self-registered users start as **viewer**. Admins promote roles via `PATCH /users/{user_id}`.

---

###  Soft Delete

Deleted records are **not physically removed** from the database.
They are flagged with `is_deleted = true` and excluded from all queries.
This preserves audit history while keeping the API surface clean.
""",
    version="1.0.0",
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Finance Dashboard API is running"}


# --- Global exception handler ---
# Catches any unhandled server-side error and returns a consistent JSON envelope
# instead of a raw 500 traceback or an empty response.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# --- Override OpenAPI schema to use clean BearerAuth instead of OAuth2 form ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the JWT token from POST /auth/login (without 'Bearer ' prefix)",
        }
    }

    # Apply BearerAuth globally to all routes
    schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
