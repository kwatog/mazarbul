from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from .database import Base, engine, SessionLocal
from . import models, schemas, auth
from .routers import (
    auth as auth_router,
    users,
    user_groups,
    record_access,
    audit_logs,
    purchase_orders,
    business_cases,
    wbs,
    assets,
    goods_receipts,
    resources,
    allocations,
    alerts
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mazarbul API")

# Enable CORS for frontend
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Development fallback
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mazarbul"}

app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(user_groups.router)
app.include_router(record_access.router)
app.include_router(audit_logs.router)
app.include_router(purchase_orders.router)
app.include_router(business_cases.router)
app.include_router(wbs.router)
app.include_router(assets.router)
app.include_router(goods_receipts.router)
app.include_router(resources.router)
app.include_router(allocations.router)
app.include_router(alerts.router)

# Initialize default admin if no users exist
@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        user_count = db.query(models.User).count()
        if user_count == 0:
            from datetime import datetime
            from .auth import get_password_hash
            admin_user = models.User(
                username="admin",
                email="admin@mazarbul.com",
                hashed_password=get_password_hash("Admin123!"), # Change this immediately
                full_name="System Admin",
                role="Admin",
                created_at=datetime.utcnow().isoformat()
            )
            db.add(admin_user)
            db.commit()
            print("Default admin created: username=admin, password=Admin123!")
    except Exception as e:
        print(f"Error creating default admin: {e}")
    finally:
        db.close()