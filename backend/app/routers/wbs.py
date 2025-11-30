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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.WBS).all()

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
    db_wbs = models.WBS(
        **wbs.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_wbs)
    db.commit()
    db.refresh(db_wbs)
    return db_wbs

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
