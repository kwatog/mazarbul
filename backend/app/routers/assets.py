from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change, user_in_owner_group

router = APIRouter(prefix="/assets", tags=["assets"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    """Get all group IDs the user belongs to."""
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def get_accessible_asset_ids(db: Session, user: models.User) -> List[int]:
    """
    Get all asset IDs the user can access based on:
    1. Owner-group membership
    2. Explicit RecordAccess grants (user or group)
    3. Records the user created
    """
    if user.role in ["Admin", "Manager"]:
        # Admins/Managers see all
        all_assets = db.query(models.Asset.id).all()
        return [a[0] for a in all_assets]
    
    # Get user's group IDs
    user_group_ids = get_user_group_ids(db, user.id)
    
    # Get assets where user is in owner_group
    owned_assets = db.query(models.Asset.id).filter(
        models.Asset.owner_group_id.in_(user_group_ids)
    ).all()
    owned_ids = [a[0] for a in owned_assets]
    
    # Get assets user created
    created_assets = db.query(models.Asset.id).filter(
        models.Asset.created_by == user.id
    ).all()
    created_ids = [a[0] for a in created_assets]
    
    # Get explicit user RecordAccess grants
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "Asset",
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    # Get group RecordAccess grants
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "Asset",
        models.RecordAccess.group_id.in_(user_group_ids),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    # Combine all accessible IDs
    accessible_ids = set(owned_ids + created_ids)
    for access in user_access + group_access:
        accessible_ids.add(access.record_id)
    
    return list(accessible_ids)

@router.get("/", response_model=List[schemas.Asset])
def list_assets(
    skip: int = 0,
    limit: int = 100,
    wbs_id: Optional[int] = None,
    owner_group_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all assets with pagination and filtering.
    
    For non-admin users, only returns assets they can access via:
    - Owner-group membership
    - Explicit RecordAccess grants
    - Records they created
    """
    # Get accessible asset IDs
    accessible_ids = get_accessible_asset_ids(db, current_user)
    
    # Start query with access filter
    query = db.query(models.Asset).filter(models.Asset.id.in_(accessible_ids))
    
    # Apply additional filters
    if wbs_id is not None:
        query = query.filter(models.Asset.wbs_id == wbs_id)
    if owner_group_id is not None:
        query = query.filter(models.Asset.owner_group_id == owner_group_id)
    if status is not None:
        query = query.filter(models.Asset.status == status)
    
    # Order by created_at descending
    query = query.order_by(models.Asset.created_at.desc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

@router.get("/{asset_id}", response_model=schemas.Asset)
def get_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Asset", "asset_id", "Read"))
):
    asset = db.query(models.Asset).get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/", response_model=schemas.Asset)
@audit_log_change(action="CREATE", table_name="asset")
async def create_asset(
    asset: schemas.AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get parent WBS to inherit owner_group_id
    wbs = db.get(models.WBS, asset.wbs_id)
    if not wbs:
        raise HTTPException(status_code=404, detail="Parent WBS not found")

    if current_user.role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create assets")

    if current_user.role not in ["Admin", "Manager"]:
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [m.group_id for m in user_groups]

        if wbs.owner_group_id not in group_ids:
            wbs_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == "WBS",
                models.RecordAccess.record_id == wbs.id,
                (
                    (models.RecordAccess.user_id == current_user.id) |
                    (models.RecordAccess.group_id.in_(group_ids))
                ),
                models.RecordAccess.access_level.in_(["Write", "Full"]),
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()

            if not wbs_access:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to create records under this parent. You must be in the owner group or have Write/Full access."
                )

    # Create Asset with inherited owner_group_id (ignore client-provided value)
    db_asset = models.Asset(
        **asset.model_dump(exclude={'owner_group_id'}),
        owner_group_id=wbs.owner_group_id,  # Inherit from parent
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.put("/{asset_id}", response_model=schemas.Asset)
@audit_log_change(action="UPDATE", table_name="asset")
async def update_asset(
    asset_id: int,
    asset_update: schemas.AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Asset", "asset_id", "Write"))
):
    """Update an existing asset."""
    asset = db.query(models.Asset).get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Apply updates (only provided fields)
    data = asset_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(asset, k, v)
    asset.updated_by = current_user.id
    asset.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/{asset_id}")
@audit_log_change(action="DELETE", table_name="asset")
async def delete_asset(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Asset", "asset_id", "Full"))
):
    asset = db.query(models.Asset).get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
    return {"status": "deleted", "id": asset_id}
