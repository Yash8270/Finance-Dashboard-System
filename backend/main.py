from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from db import engine, Base

# Import all models so SQLAlchemy registers them before create_all
import models.user  # noqa: F401
import models.record  # noqa: F401


from routes import auth, users, records, dashboard

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Dashboard API",
    description="""
## Finance Dashboard — Role-Based REST API

A clean JWT-authenticated API with Role-Based Access Control (RBAC).

---

###  How to Authenticate in Swagger

1. Call **POST /auth/login** with your email and password
2. Copy the `access_token` from the response
3. Click the **Authorize ** button at the top
4. Enter: `Bearer <your_token>` in the value field
5. Click **Authorize** — all protected routes are now unlocked

---

### Role Permissions

| Role     | Access |
|----------|--------|
| `viewer`  | Dashboard APIs only |
| `analyst` | Dashboard + view records |
| `admin`   | Full access |
""",
    version="1.0.0",
)

# CORS — allow all origins for simplicity (adjust in production)
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

    # Replace any auto-generated OAuth2 security schemes
    # with a clean HTTP Bearer token scheme
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
