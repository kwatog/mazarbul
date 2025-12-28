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
    skip: int = 0,
    limit: int = 100,
    resource_id: int = None,
    po_id: int = None,
    owner_group_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all resource-PO allocations with pagination and filtering."""
    query = db.query(models.ResourcePOAllocation)

    # Apply filters
    if resource_id:
        query = query.filter(models.ResourcePOAllocation.resource_id == resource_id)
    if po_id:
        query = query.filter(models.ResourcePOAllocation.po_id == po_id)
    if owner_group_id:
        query = query.filter(models.ResourcePOAllocation.owner_group_id == owner_group_id)

    # Order by created_at descending
    query = query.order_by(models.ResourcePOAllocation.created_at.desc())

    # Apply pagination
    return query.offset(skip).limit(limit).all()

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
    # Get parent PO to inherit owner_group_id
    po = db.get(models.PurchaseOrder, alloc.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Parent purchase order not found")

    # Create allocation with inherited owner_group_id (ignore client-provided value)
    db_alloc = models.ResourcePOAllocation(
        **alloc.model_dump(exclude={'owner_group_id'}),
        owner_group_id=po.owner_group_id,  # Inherit from parent
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_alloc)
    db.commit()
    db.refresh(db_alloc)
    return db_alloc

@router.put("/{alloc_id}", response_model=schemas.ResourcePOAllocation)
@audit_log_change(action="UPDATE", table_name="resource_po_allocation")
async def update_allocation(
    alloc_id: int,
    alloc_update: schemas.ResourcePOAllocationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("ResourcePOAllocation", "alloc_id", "Write"))
):
    """Update an existing resource-PO allocation."""
    alloc = db.query(models.ResourcePOAllocation).get(alloc_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="ResourcePOAllocation not found")

    # Apply updates (only provided fields)
    data = alloc_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(alloc, k, v)
    alloc.updated_by = current_user.id
    alloc.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(alloc)
    return alloc

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
