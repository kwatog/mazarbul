from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    """Get all group IDs the user belongs to."""
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def get_accessible_po_ids(db: Session, user: models.User) -> List[int]:
    """
    Get all PO IDs the user can access based on:
    1. Owner-group membership
    2. Explicit RecordAccess grants (user or group)
    3. Records the user created
    """
    if user.role in ["Admin", "Manager"]:
        all_pos = db.query(models.PurchaseOrder.id).all()
        return [p[0] for p in all_pos]
    
    user_group_ids = get_user_group_ids(db, user.id)
    
    owned_pos = db.query(models.PurchaseOrder.id).filter(
        models.PurchaseOrder.owner_group_id.in_(user_group_ids)
    ).all()
    owned_ids = [p[0] for p in owned_pos]
    
    created_pos = db.query(models.PurchaseOrder.id).filter(
        models.PurchaseOrder.created_by == user.id
    ).all()
    created_ids = [p[0] for p in created_pos]
    
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "PurchaseOrder",
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "PurchaseOrder",
        models.RecordAccess.group_id.in_(user_group_ids),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    accessible_ids = set(owned_ids + created_ids)
    for access in user_access + group_access:
        accessible_ids.add(access.record_id)
    
    return list(accessible_ids)

@router.get("/", response_model=List[schemas.PurchaseOrder])
def list_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    owner_group_id: Optional[int] = None,
    supplier: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all purchase orders with pagination and filtering.
    
    For non-admin users, only returns POs they can access via:
    - Owner-group membership
    - Explicit RecordAccess grants
    - Records they created
    """
    accessible_ids = get_accessible_po_ids(db, current_user)
    
    query = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id.in_(accessible_ids))

    if status is not None:
        query = query.filter(models.PurchaseOrder.status == status)
    if owner_group_id is not None:
        query = query.filter(models.PurchaseOrder.owner_group_id == owner_group_id)
    if supplier is not None:
        query = query.filter(models.PurchaseOrder.supplier.ilike(f"%{supplier}%"))

    query = query.order_by(models.PurchaseOrder.created_at.desc())

    return query.offset(skip).limit(limit).all()

@router.get("/{po_id}", response_model=schemas.PurchaseOrder)
def get_purchase_order(
    po_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("PurchaseOrder", "po_id", "Read"))
):
    po = db.query(models.PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    return po

@router.post("/", response_model=schemas.PurchaseOrder)
@audit_log_change(action="CREATE", table_name="purchase_order")
async def create_purchase_order(
    po: schemas.PurchaseOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get parent Asset to inherit owner_group_id
    asset = db.get(models.Asset, po.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Parent asset not found")

    if current_user.role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create purchase orders")

    if current_user.role not in ["Admin", "Manager"]:
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [m.group_id for m in user_groups]

        if asset.owner_group_id not in group_ids:
            asset_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == "Asset",
                models.RecordAccess.record_id == asset.id,
                (
                    (models.RecordAccess.user_id == current_user.id) |
                    (models.RecordAccess.group_id.in_(group_ids))
                ),
                models.RecordAccess.access_level.in_(["Write", "Full"]),
                (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
            ).first()

            if not asset_access:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to create records under this parent. You must be in the owner group or have Write/Full access."
                )

    # Create PO with inherited owner_group_id (ignore client-provided value)
    db_po = models.PurchaseOrder(
        **po.model_dump(exclude={'owner_group_id'}),
        owner_group_id=asset.owner_group_id,  # Inherit from parent
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po

@router.delete("/{po_id}")
@audit_log_change(action="DELETE", table_name="purchase_order")
async def delete_purchase_order(
    po_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("PurchaseOrder", "po_id", "Full"))
):
    po = db.query(models.PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    db.delete(po)
    db.commit()
    return {"status": "deleted", "id": po_id}

@router.put("/{po_id}", response_model=schemas.PurchaseOrder)
@audit_log_change(action="UPDATE", table_name="purchase_order")
async def update_purchase_order(
    po_id: int,
    po_update: schemas.PurchaseOrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("PurchaseOrder", "po_id", "Write"))
):
    po = db.query(models.PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")

    # Apply updates (only provided fields)
    data = po_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(po, k, v)
    po.updated_by = current_user.id
    po.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(po)
    return po
