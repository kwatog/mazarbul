import json
import base64
import re
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, verify_password, get_password_hash, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password against policy. Returns (is_valid, error_message)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
    
    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Only Admin can register new users
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can register new users")

    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Validate password against policy
    is_valid, error_msg = validate_password(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        full_name=user.full_name,
        department=user.department,
        role=user.role,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.UserResponse)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow().isoformat()
    db.commit()

    # Create access token with longer expiry for cookie storage
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    # Set HttpOnly cookie (secure=False for localhost/development)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )
    
    # Set user info cookie (not HttpOnly for frontend access) - use base64 to avoid escaping issues
    user_info = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department
    }
    user_info_b64 = base64.b64encode(json.dumps(user_info).encode()).decode()
    response.set_cookie(
        key="user_info",
        value=user_info_b64,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Login successful", "user": user}

@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using existing HttpOnly cookie"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token found in cookies"
        )
    
    # Verify current token and get user
    try:
        from ..auth import get_current_user_from_token
        user = get_current_user_from_token(token, db)
    except HTTPException:
        # Token is invalid/expired, clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("user_info")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid"
        )
    
    # Generate new token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    # Update cookies with new token
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Update user info cookie - use base64 to avoid escaping issues
    user_info = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department
    }
    user_info_b64 = base64.b64encode(json.dumps(user_info).encode()).decode()
    response.set_cookie(
        key="user_info",
        value=user_info_b64,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"message": "Token refreshed successfully"}

@router.post("/logout")
def logout(response: Response):
    """Logout user by clearing HttpOnly cookies"""
    response.delete_cookie("access_token")
    response.delete_cookie("user_info")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
def update_users_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update current user's profile (full_name, department). Cannot change username or role."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.department is not None:
        current_user.department = user_update.department
    
    current_user.updated_by = current_user.id
    current_user.updated_at = datetime.utcnow().isoformat()
    
    db.commit()
    db.refresh(current_user)
    return current_user

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/password")
def change_password(
    password_change: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Change current user's password. Requires current password for verification."""
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password against policy
    is_valid, error_msg = validate_password(password_change.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Hash and update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    current_user.updated_by = current_user.id
    current_user.updated_at = datetime.utcnow().isoformat()
    
    db.commit()
    
    return {"message": "Password changed successfully"}
