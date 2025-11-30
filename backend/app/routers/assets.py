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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Asset).all()

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
    db_asset = models.Asset(
        **asset.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

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
