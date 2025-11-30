from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/allocations", tags=["allocations"])

@router.get("/", response_model=List[schemas.ResourcePOAllocation])
def list_allocations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.ResourcePOAllocation).all()

@router.get("/{alloc_id}", response_model=schemas.ResourcePOAllocation)
def get_allocation(
    alloc_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("ResourcePOAllocation", "alloc_id", "Read"))
):
    alloc = db.query(models.ResourcePOAllocation).get(alloc_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="ResourcePOAllocation not found")
    return alloc

@router.post("/", response_model=schemas.ResourcePOAllocation)
@audit_log_change(action="CREATE", table_name="resource_po_allocation")
async def create_allocation(
    alloc: schemas.ResourcePOAllocationCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_alloc = models.ResourcePOAllocation(
        **alloc.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_alloc)
    db.commit()
    db.refresh(db_alloc)
    return db_alloc

@router.delete("/{alloc_id}")
@audit_log_change(action="DELETE", table_name="resource_po_allocation")
async def delete_allocation(
    alloc_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("ResourcePOAllocation", "alloc_id", "Full"))
):
    alloc = db.query(models.ResourcePOAllocation).get(alloc_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="ResourcePOAllocation not found")
    db.delete(alloc)
    db.commit()
    return {"status": "deleted", "id": alloc_id}
