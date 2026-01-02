from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/allocations", tags=["allocations"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def get_accessible_allocation_ids(db: Session, user: models.User) -> List[int]:
    if user.role in ["Admin", "Manager"]:
        all_allocs = db.query(models.ResourcePOAllocation.id).all()
        return [a[0] for a in all_allocs]
    
    user_group_ids = get_user_group_ids(db, user.id)
    
    owned_allocs = db.query(models.ResourcePOAllocation.id).filter(
        models.ResourcePOAllocation.owner_group_id.in_(user_group_ids)
    ).all()
    owned_ids = [a[0] for a in owned_allocs]
    
    created_allocs = db.query(models.ResourcePOAllocation.id).filter(
        models.ResourcePOAllocation.created_by == user.id
    ).all()
    created_ids = [a[0] for a in created_allocs]
    
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "ResourcePOAllocation",
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "ResourcePOAllocation",
        models.RecordAccess.group_id.in_(user_group_ids),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    accessible_ids = set(owned_ids + created_ids)
    for access in user_access + group_access:
        accessible_ids.add(access.record_id)
    
    return list(accessible_ids)

@router.get("/", response_model=List[schemas.ResourcePOAllocation])
def list_allocations(
    skip: int = 0,
    limit: int = 100,
    resource_id: Optional[int] = None,
    po_id: Optional[int] = None,
    owner_group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all resource-PO allocations with pagination and filtering.
    
    For non-admin users, only returns allocations they can access via:
    - Owner-group membership
    - Explicit RecordAccess grants
    - Records they created
    """
    accessible_ids = get_accessible_allocation_ids(db, current_user)
    
    query = db.query(models.ResourcePOAllocation).filter(
        models.ResourcePOAllocation.id.in_(accessible_ids)
    )

    if resource_id is not None:
        query = query.filter(models.ResourcePOAllocation.resource_id == resource_id)
    if po_id is not None:
        query = query.filter(models.ResourcePOAllocation.po_id == po_id)
    if owner_group_id is not None:
        query = query.filter(models.ResourcePOAllocation.owner_group_id == owner_group_id)

    query = query.order_by(models.ResourcePOAllocation.created_at.desc())

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
    resource = db.get(models.Resource, alloc.resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Parent resource not found")

    po = db.get(models.PurchaseOrder, alloc.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Parent purchase order not found")

    if current_user.role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create allocations")

    if current_user.role not in ["Admin", "Manager"]:
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [m.group_id for m in user_groups]

        resource_access = None
        po_access = None

        if resource.owner_group_id not in group_ids:
            resource_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == "Resource",
                models.RecordAccess.record_id == resource.id,
                (
                    (models.RecordAccess.user_id == current_user.id) |
                    (models.RecordAccess.group_id.in_(group_ids))
                ),
                models.RecordAccess.access_level.in_(["Write", "Full"]),
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()

        if po.owner_group_id not in group_ids:
            po_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == "PurchaseOrder",
                models.RecordAccess.record_id == po.id,
                (
                    (models.RecordAccess.user_id == current_user.id) |
                    (models.RecordAccess.group_id.in_(group_ids))
                ),
                models.RecordAccess.access_level.in_(["Write", "Full"]),
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()

        if resource.owner_group_id not in group_ids and not resource_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to the parent Resource. You must be in the owner group or have Write/Full access."
            )
        if po.owner_group_id not in group_ids and not po_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to the parent Purchase Order. You must be in the owner group or have Write/Full access."
            )

    db_alloc = models.ResourcePOAllocation(
        **alloc.model_dump(exclude={'owner_group_id'}),
        owner_group_id=po.owner_group_id,
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
    alloc = db.query(models.ResourcePOAllocation).get(alloc_id)
    if not alloc:
        raise HTTPException(status_code=404, detail="ResourcePOAllocation not found")

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
