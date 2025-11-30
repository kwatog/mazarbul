from datetime import datetime, timedelta
from typing import Optional, Union
import json
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
            
        # Check if user is creator (has full access)
        # We need to dynamically find the model
        model_cls = getattr(models, record_type, None)
        if model_cls:
            record = db.query(model_cls).get(record_id)
            if record and hasattr(record, 'created_by') and record.created_by == current_user.id:
                return current_user
            
        # Check explicit record access grants
        access_levels = {"Read": 0, "Write": 1, "Full": 2}
        req_level_val = access_levels.get(required_access, 2)
        
        # Check direct user access
        user_access = db.query(models.RecordAccess).filter(
            models.RecordAccess.record_type == record_type,
            models.RecordAccess.record_id == record_id,
            models.RecordAccess.user_id == current_user.id,
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
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
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()
            
            if group_access and access_levels.get(group_access.access_level, 0) >= req_level_val:
                return current_user
                
        # Check department access for User role
        # Requires fetching the record again if not fetched
        if current_user.role == "User":
             if not model_cls: 
                 model_cls = getattr(models, record_type, None)
             if model_cls:
                record = db.query(model_cls).get(record_id)
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
    Requires 'current_user' and 'db' to be in the function kwargs.
    """
    def audit_decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            request = kwargs.get('request') # Try to get request if available

            # Pre-fetch old values for Update/Delete
            old_values = None
            record_id = None
            
            # Need to identify record_id from args/kwargs usually
            # This is tricky for generic usage. 
            # We will assume the function returns the modified object.
            
            result = await func(*args, **kwargs)
            
            if current_user and db:
                # Determine record ID
                if hasattr(result, 'id'):
                    record_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    record_id = result['id']
                
                # Determine new values (simple dump)
                new_vals = None
                if action in ['CREATE', 'UPDATE']:
                    if hasattr(result, 'model_dump'):
                        new_vals = result.model_dump()
                    elif hasattr(result, '__dict__'):
                         # SQLAlchemy object
                         new_vals = {k:v for k,v in result.__dict__.items() if not k.startswith('_')}
                
                if record_id:
                    audit_entry = models.AuditLog(
                        table_name=table_name,
                        record_id=record_id,
                        action=action,
                        old_values=json.dumps(old_values, default=str) if old_values else None,
                        new_values=json.dumps(new_vals, default=str) if new_vals else None,
                        user_id=current_user.id,
                        timestamp=datetime.utcnow().isoformat(),
                        ip_address=None # Difficult to get without Request context cleanly passed everywhere
                    )
                    db.add(audit_entry)
                    db.commit()
                
            return result
        return wrapper
    return audit_decorator
