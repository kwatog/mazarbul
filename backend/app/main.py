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
    budget_items,
    purchase_orders,
    business_cases,
    business_case_line_items,
    wbs,
    assets,
    goods_receipts,
    resources,
    allocations,
    alerts
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ebrose API", debug=True)

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
    return {"status": "ok", "service": "ebrose"}

app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(user_groups.router)
app.include_router(record_access.router)
app.include_router(audit_logs.router)
app.include_router(budget_items.router)
app.include_router(purchase_orders.router)
app.include_router(business_cases.router)
app.include_router(business_case_line_items.router)
app.include_router(wbs.router)
app.include_router(assets.router)
app.include_router(goods_receipts.router)
app.include_router(resources.router)
app.include_router(allocations.router)
app.include_router(alerts.router)

# Initialize admin user from environment variables if no users exist
@app.on_event("startup")
def create_default_admin():
    # Only create admin if explicitly enabled via environment
    if not os.getenv("CREATE_ADMIN_USER", "").lower() in ["true", "1", "yes"]:
        return
    
    db = SessionLocal()
    try:
        user_count = db.query(models.User).count()
        if user_count == 0:
            from datetime import datetime
            from .auth import get_password_hash
            
            # Get admin credentials from environment
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD")
            admin_email = os.getenv("ADMIN_EMAIL", "admin@ebrose.local")
            admin_full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator")
            
            if not admin_password:
                print("ERROR: ADMIN_PASSWORD environment variable required for admin creation")
                return
                
            if len(admin_password) < 8:
                print("ERROR: ADMIN_PASSWORD must be at least 8 characters long")
                return
            
            admin_user = models.User(
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                full_name=admin_full_name,
                role="Admin",
                created_at=datetime.utcnow().isoformat()
            )
            db.add(admin_user)
            db.commit()
            print(f"Admin user '{admin_username}' created successfully")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()
