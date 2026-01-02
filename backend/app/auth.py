from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import json
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

def now_utc() -> str:
    """Get current UTC timestamp as ISO string. Replaces deprecated datetime.now(timezone.utc)."""
    return datetime.now(timezone.utc).isoformat()

def now_utc_datetime() -> datetime:
    """Get current UTC datetime. Use when you need a datetime object, not a string."""
    return datetime.now(timezone.utc)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment in ["production", "prod", "staging"]:
        raise ValueError("SECRET_KEY environment variable is required for production deployments")
    SECRET_KEY = "development-fallback-key-change-for-production"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=14)
# We use OAuth2PasswordBearer for Swagger UI compatibility, but logic allows custom header too
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def user_in_owner_group(user: "models.User", owner_group_id: int, db: Session, required_level: str = "Read") -> bool:
    """
    Check if user has access to records owned by a specific group.
    Returns True if:
    - User is a member of the owner_group_id
    - Admin/Manager roles have automatic access
    """
    # Admin and Manager have access to all groups
    if user.role in ["Admin", "Manager"]:
        return True

    # Check if user is a member of the owner group
    membership = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user.id,
        models.UserGroupMembership.group_id == owner_group_id
    ).first()

    return membership is not None

def check_business_case_access(user: "models.User", business_case: "models.BusinessCase", db: Session, required_level: str = "Read") -> bool:
    """
    Hybrid BusinessCase access control:
    1. Creator access (audit only): Creator has Read always, NOT Write
    2. Line-item based access (PRIMARY): Access via budget items linked through line items
    3. lead_group_id access: If BC has lead_group_id, user must be member for Write access
    4. Explicit RecordAccess (OVERRIDE): Direct grants for audits/reviews
    """
    access_levels = {"Read": 0, "Write": 1, "Full": 2}
    user_group_ids = [
        m.group_id
        for m in db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == user.id
        ).all()
    ]

    # 1. Creator access (audit only - Read only, not Write)
    if business_case.created_by == user.id:
        if required_level == "Read":
            return True
        # Creator does NOT get Write access - they must have access via line items or explicit grants

    # 2. lead_group_id enforcement for Write access
    if required_level in ["Write", "Full"] and business_case.lead_group_id:
        if required_level == "Write" and user_in_owner_group(user, business_case.lead_group_id, db, required_level):
            return True
        # Not a member - check explicit access
        bc_access = db.query(models.RecordAccess).filter(
            models.RecordAccess.record_type == "BusinessCase",
            models.RecordAccess.record_id == business_case.id,
            (
                (models.RecordAccess.user_id == user.id) |
                (models.RecordAccess.group_id.in_(user_group_ids))
            ),
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
        ).first()

        if not bc_access or access_levels.get(bc_access.access_level, 0) < access_levels.get(required_level, 2):
            return False

    # 3. Line-item based access (PRIMARY - per spec)
    for line_item in business_case.line_items:
        budget_item = line_item.budget_item
        if budget_item and budget_item.owner_group_id:
            if user_in_owner_group(user, budget_item.owner_group_id, db, required_level):
                return True

        # Check explicit budget item access
        budget_access = db.query(models.RecordAccess).filter(
            models.RecordAccess.record_type == "BudgetItem",
            models.RecordAccess.record_id == budget_item.id,
            (
                (models.RecordAccess.user_id == user.id) |
                (models.RecordAccess.group_id.in_(user_group_ids))
            ),
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
        ).first()

        if budget_access:
            if access_levels.get(budget_access.access_level, 0) >= access_levels.get(required_level, 2):
                return True

    # 4. Explicit BC access (OVERRIDE)
    bc_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "BusinessCase",
        models.RecordAccess.record_id == business_case.id,
        (
            (models.RecordAccess.user_id == user.id) |
            (models.RecordAccess.group_id.in_(user_group_ids))
        ),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
    ).first()

    if bc_access:
        if access_levels.get(bc_access.access_level, 0) >= access_levels.get(required_level, 2):
            return True

    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str, db: Session):
    """Extract user from JWT token - used by refresh endpoint"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Get current user from HttpOnly cookie"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication cookie found"
        )
    return get_current_user_from_token(token, db)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current user - try cookie first, then Authorization header"""
    # Try HttpOnly cookie first
    token = request.cookies.get("access_token")
    
    if not token:
        # Fallback to Authorization header for API clients/Swagger
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication found"
        )
    
    return get_current_user_from_token(token, db)

def require_role(required_role: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        role_hierarchy = {"Viewer": 0, "User": 1, "Manager": 2, "Admin": 3}
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 3)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def check_record_access(record_type: str, record_id_param: str, required_access: str):
    """
    Check if current user has required access to specific record.
    record_id_param: The name of the path parameter containing the ID (e.g., 'po_id', 'wbs_id')
    Access levels: Read < Write < Full
    """
    def access_checker(
        request: Request,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Extract record_id from path params
        record_id = request.path_params.get(record_id_param)
        if not record_id:
             # If we can't find ID, we assume it's a create/list operation which is handled by role
             return current_user
        
        try:
            record_id = int(record_id)
        except ValueError:
            return current_user

        # Admin has full access to everything
        if current_user.role == "Admin":
            return current_user

        # Manager has full access to everything
        if current_user.role == "Manager":
            return current_user

        access_levels = {"Read": 0, "Write": 1, "Full": 2}
        role_caps = {"Viewer": 0, "User": 1, "Manager": 2, "Admin": 2}
        if access_levels.get(required_access, 2) > role_caps.get(current_user.role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # Fetch the record to check owner_group_id and creator
        model_cls = getattr(models, record_type, None)
        record = None
        if model_cls:
            record = db.get(model_cls, record_id)

            # Check if user is creator (has full access)
            if record and hasattr(record, 'created_by') and record.created_by == current_user.id:
                return current_user

            # CRITICAL: Check owner_group_id membership (default Read/Write access)
            if record and hasattr(record, 'owner_group_id') and record.owner_group_id:
                if user_in_owner_group(current_user, record.owner_group_id, db, required_access):
                    return current_user

        # Check explicit record access grants
        req_level_val = access_levels.get(required_access, 2)
        
        # Check direct user access
        user_access = db.query(models.RecordAccess).filter(
            models.RecordAccess.record_type == record_type,
            models.RecordAccess.record_id == record_id,
            models.RecordAccess.user_id == current_user.id,
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
        ).first()
        
        if user_access and access_levels.get(user_access.access_level, 0) >= req_level_val:
            return current_user
            
        # Check group access
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        
        for membership in user_groups:
            group_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == record_type,
                models.RecordAccess.record_id == record_id,
                models.RecordAccess.group_id == membership.group_id,
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
            ).first()
            
            if group_access and access_levels.get(group_access.access_level, 0) >= req_level_val:
                return current_user
                
        # Check department access for User role
        # Requires fetching the record again if not fetched
        if current_user.role == "User":
             if not model_cls:
                 model_cls = getattr(models, record_type, None)
             if model_cls:
                record = db.get(model_cls, record_id)
                if record and hasattr(record, 'dept'):
                    if record.dept == current_user.department and required_access in ["Read", "Write"]:
                        return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient {required_access} access to {record_type} {record_id}"
        )
        
    return access_checker

def audit_log_change(action: str, table_name: str):
    """
    Decorator to log changes.
    Requires the decorated function to return a SQLAlchemy model instance or a dict with 'id'.
    Requires 'current_user', 'db', and optionally 'id' or record_id in kwargs/args.
    For CREATE: ensure db.flush() is called to generate ID before audit log.
    """
    def audit_decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            request = kwargs.get('request')

            old_values = None
            record_id = None

            # For UPDATE/DELETE: pre-fetch old values BEFORE the operation
            if action in ['UPDATE', 'DELETE']:
                # Try to extract record_id from kwargs
                record_id = kwargs.get('id') or kwargs.get(f'{table_name}_id') or kwargs.get('bc_id') or kwargs.get('wbs_id') or kwargs.get('po_id') or kwargs.get('asset_id') or kwargs.get('gr_id') or kwargs.get('resource_id') or kwargs.get('alloc_id')
                if record_id and db:
                    model_cls = getattr(models, table_name.title().replace('_', ''), None)
                    if model_cls:
                        record = db.get(model_cls, record_id)
                        if record and hasattr(record, '__dict__'):
                            old_values = {k: v for k, v in record.__dict__.items() if not k.startswith('_')}
                        elif record and hasattr(record, 'model_dump'):
                            old_values = record.model_dump()

            result = await func(*args, **kwargs)

            if current_user and db:
                # Determine record ID from result
                if hasattr(result, 'id'):
                    record_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    record_id = result['id']

                # Ensure record_id is available for CREATE (requires db.flush() in the route)
                if not record_id:
                    return result

                # Determine new values
                new_vals = None
                if action in ['CREATE', 'UPDATE']:
                    if hasattr(result, 'model_dump'):
                        new_vals = result.model_dump()
                    elif hasattr(result, '__dict__'):
                        new_vals = {k: v for k, v in result.__dict__.items() if not k.startswith('_')}

                # Add audit log entry
                audit_entry = models.AuditLog(
                    table_name=table_name,
                    record_id=record_id,
                    action=action,
                    old_values=json.dumps(old_values, default=str) if old_values else None,
                    new_values=json.dumps(new_vals, default=str) if new_vals else None,
                    user_id=current_user.id,
                    timestamp=now_utc(),
                    ip_address=None
                )
                db.add(audit_entry)
                db.commit()

            return result
        return wrapper
    return audit_decorator
