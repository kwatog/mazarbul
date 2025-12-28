from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get("/", response_model=List[schemas.Asset])
def list_assets(
    skip: int = 0,
    limit: int = 100,
    wbs_id: int = None,
    owner_group_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all assets with pagination and filtering."""
    query = db.query(models.Asset)

    # Apply filters
    if wbs_id:
        query = query.filter(models.Asset.wbs_id == wbs_id)
    if owner_group_id:
        query = query.filter(models.Asset.owner_group_id == owner_group_id)
    if status:
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
