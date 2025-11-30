from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, require_role

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

@router.get("/", response_model=List[schemas.AuditLog])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    # By default limit to last 100 to avoid performance hit
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(100).all()

@router.get("/{record_type}/{record_id}", response_model=List[schemas.AuditLog])
def get_record_history(
    record_type: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("User"))
):
    # Users can see history of records they can see? 
    # For simplicity, let's just allow "User" role to see history if they know the ID.
    return db.query(models.AuditLog).filter(
        models.AuditLog.table_name == record_type, # Note: mapping might be needed if table name != record type
        models.AuditLog.record_id == record_id
    ).order_by(models.AuditLog.timestamp.desc()).all()
