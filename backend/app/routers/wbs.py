from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/wbs", tags=["wbs"])

@router.get("/", response_model=List[schemas.WBS])
def list_wbs(
    skip: int = 0,
    limit: int = 100,
    business_case_line_item_id: int = None,
    owner_group_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all WBS items with pagination and filtering."""
    query = db.query(models.WBS)

    # CRITICAL: Filter by owner_group_id access (only show records user can access)
    if current_user.role not in ["Admin", "Manager"]:
        # Get all groups the user is a member of
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [membership.group_id for membership in user_groups]

        # Filter to accessible records
        accessible_ids_query = db.query(models.WBS.id).filter(
            (models.WBS.owner_group_id.in_(group_ids)) |
            (models.WBS.created_by == current_user.id)
        )

        # Add explicit RecordAccess grants
        explicit_access = db.query(models.RecordAccess.record_id).filter(
            models.RecordAccess.record_type == "WBS",
            models.RecordAccess.user_id == current_user.id,
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
        )

        accessible_ids = [item.id for item in accessible_ids_query.all()]
        accessible_ids += [access.record_id for access in explicit_access.all()]

        query = query.filter(models.WBS.id.in_(accessible_ids))

    # Apply filters
    if business_case_line_item_id:
        query = query.filter(models.WBS.business_case_line_item_id == business_case_line_item_id)
    if owner_group_id:
        query = query.filter(models.WBS.owner_group_id == owner_group_id)
    if status:
        query = query.filter(models.WBS.status == status)

    # Order by created_at descending
    query = query.order_by(models.WBS.created_at.desc())

    # Apply pagination
    return query.offset(skip).limit(limit).all()

@router.get("/{wbs_id}", response_model=schemas.WBS)
def get_wbs(
    wbs_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("WBS", "wbs_id", "Read"))
):
    wbs = db.query(models.WBS).get(wbs_id)
    if not wbs:
        raise HTTPException(status_code=404, detail="WBS not found")
    return wbs

@router.post("/", response_model=schemas.WBS)
@audit_log_change(action="CREATE", table_name="wbs")
async def create_wbs(
    wbs: schemas.WBSCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get parent line item
    line_item = db.get(models.BusinessCaseLineItem, wbs.business_case_line_item_id)
    if not line_item:
        raise HTTPException(status_code=404, detail="Parent business case line item not found")
    
    # Validate parent access - require Write/Full access to the parent line item
    if current_user.role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create WBS items")

    if current_user.role not in ["Admin", "Manager"]:
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [m.group_id for m in user_groups]

        if line_item.owner_group_id not in group_ids:
            line_item_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == "BusinessCaseLineItem",
                models.RecordAccess.record_id == line_item.id,
                (
                    (models.RecordAccess.user_id == current_user.id) |
                    (models.RecordAccess.group_id.in_(group_ids))
                ),
                models.RecordAccess.access_level.in_(["Write", "Full"]),
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()

            if not line_item_access:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to create records under this parent. You must be in the owner group or have Write/Full access."
                )

    # Create WBS with inherited owner_group_id (ignore client-provided value)
    db_wbs = models.WBS(
        **wbs.model_dump(exclude={'owner_group_id'}),
        owner_group_id=line_item.owner_group_id,  # Inherit from parent
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_wbs)
    db.commit()
    db.refresh(db_wbs)
    return db_wbs

@router.put("/{wbs_id}", response_model=schemas.WBS)
@audit_log_change(action="UPDATE", table_name="wbs")
async def update_wbs(
    wbs_id: int,
    wbs_update: schemas.WBSUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("WBS", "wbs_id", "Write"))
):
    """Update an existing WBS item."""
    wbs = db.query(models.WBS).get(wbs_id)
    if not wbs:
        raise HTTPException(status_code=404, detail="WBS not found")

    # Apply updates (only provided fields)
    data = wbs_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(wbs, k, v)
    wbs.updated_by = current_user.id
    wbs.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(wbs)
    return wbs

@router.delete("/{wbs_id}")
@audit_log_change(action="DELETE", table_name="wbs")
async def delete_wbs(
    wbs_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("WBS", "wbs_id", "Full"))
):
    wbs = db.query(models.WBS).get(wbs_id)
    if not wbs:
        raise HTTPException(status_code=404, detail="WBS not found")
    db.delete(wbs)
    db.commit()
    return {"status": "deleted", "id": wbs_id}
