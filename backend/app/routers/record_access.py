from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, require_role

router = APIRouter(prefix="/record-access", tags=["record-access"])

@router.get("/{record_type}/{record_id}", response_model=List[schemas.RecordAccess])
def get_record_access_list(
    record_type: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Simplification: Any authenticated user can see who has access to what (transparency)
    # Or restrict to those who have access. Let's allow transparency for now.
    return db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == record_type,
        models.RecordAccess.record_id == record_id
    ).all()

@router.post("/", response_model=schemas.RecordAccess)
def grant_access(
    access: schemas.RecordAccessCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate target user role - prevent Viewer from receiving Write/Full access
    if access.user_id:
        target_user = db.query(models.User).get(access.user_id)
        if target_user and target_user.role == "Viewer":
            if access.access_level in ["Write", "Full"]:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot grant Write or Full access to Viewers"
                )

    # Check if user has "Full" access to the record they are trying to share
    # We'll reuse the check_access logic but manually here since it's a bit meta

    # Logic: Admin/Manager can always grant.
    # Creator can grant.
    # Someone with 'Full' access can grant.

    if current_user.role in ["Admin", "Manager"]:
        can_grant = True
    else:
        # Check if creator
        model_cls = getattr(models, access.record_type, None)
        if not model_cls:
             raise HTTPException(status_code=400, detail="Invalid record type")

        record = db.get(model_cls, access.record_id)
        if record and hasattr(record, 'created_by') and record.created_by == current_user.id:
            can_grant = True
        else:
            # Check explicit Full access
            user_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == access.record_type,
                models.RecordAccess.record_id == access.record_id,
                models.RecordAccess.user_id == current_user.id,
                models.RecordAccess.access_level == "Full"
            ).first()
            can_grant = bool(user_access)

    if not can_grant:
        raise HTTPException(status_code=403, detail="Insufficient permissions to grant access")

    db_access = models.RecordAccess(
        **access.model_dump(),
        granted_by=current_user.id,
        granted_at=datetime.utcnow().isoformat()
    )
    db.add(db_access)
    db.commit()
    db.refresh(db_access)
    return db_access

@router.delete("/{access_id}")
def revoke_access(
    access_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    access_record = db.get(models.RecordAccess, access_id)
    if not access_record:
        raise HTTPException(status_code=404, detail="Access record not found")

    # Same logic: Admin/Manager or Creator or Full access holder can revoke
    # Simplification: Only Admin/Manager or the specific grantor can revoke for now
    if current_user.role in ["Admin", "Manager"] or access_record.granted_by == current_user.id:
         db.delete(access_record)
         db.commit()
         return {"status": "deleted"}
    
    raise HTTPException(status_code=403, detail="Not authorized to revoke this access")

@router.put("/{access_id}", response_model=schemas.RecordAccess)
def update_access(
    access_id: int,
    access_update: schemas.RecordAccessUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update existing record access permissions"""
    access_record = db.get(models.RecordAccess, access_id)
    if not access_record:
        raise HTTPException(status_code=404, detail="Access record not found")

    # Same authorization logic as revoke
    if not (current_user.role in ["Admin", "Manager"] or access_record.granted_by == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this access")

    # Update allowed fields
    if access_update.access_level is not None:
        if access_record.user_id:
            target_user = db.query(models.User).get(access_record.user_id)
            if target_user and target_user.role == "Viewer":
                if access_update.access_level in ["Write", "Full"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot grant Write or Full access to Viewers"
                    )
        access_record.access_level = access_update.access_level
    if access_update.expires_at is not None:
        access_record.expires_at = access_update.expires_at

    # Update modification tracking
    access_record.updated_by = current_user.id
    access_record.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(access_record)
    return access_record
