from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/goods-receipts", tags=["goods-receipts"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def get_accessible_gr_ids(db: Session, user: models.User) -> List[int]:
    if user.role in ["Admin", "Manager"]:
        all_grs = db.query(models.GoodsReceipt.id).all()
        return [g[0] for g in all_grs]
    
    user_group_ids = get_user_group_ids(db, user.id)
    
    owned_grs = db.query(models.GoodsReceipt.id).filter(
        models.GoodsReceipt.owner_group_id.in_(user_group_ids)
    ).all()
    owned_ids = [g[0] for g in owned_grs]
    
    created_grs = db.query(models.GoodsReceipt.id).filter(
        models.GoodsReceipt.created_by == user.id
    ).all()
    created_ids = [g[0] for g in created_grs]
    
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "GoodsReceipt",
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "GoodsReceipt",
        models.RecordAccess.group_id.in_(user_group_ids),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    accessible_ids = set(owned_ids + created_ids)
    for access in user_access + group_access:
        accessible_ids.add(access.record_id)
    
    return list(accessible_ids)

@router.get("/", response_model=List[schemas.GoodsReceipt])
def list_goods_receipts(
    skip: int = 0,
    limit: int = 100,
    po_id: Optional[int] = None,
    owner_group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all goods receipts with pagination and filtering.
    
    For non-admin users, only returns GRs they can access via:
    - Owner-group membership
    - Explicit RecordAccess grants
    - Records they created
    """
    accessible_ids = get_accessible_gr_ids(db, current_user)
    
    query = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.id.in_(accessible_ids))

    if po_id is not None:
        query = query.filter(models.GoodsReceipt.po_id == po_id)
    if owner_group_id is not None:
        query = query.filter(models.GoodsReceipt.owner_group_id == owner_group_id)

    query = query.order_by(models.GoodsReceipt.gr_date.desc())

    return query.offset(skip).limit(limit).all()

@router.get("/{gr_id}", response_model=schemas.GoodsReceipt)
def get_goods_receipt(
    gr_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("GoodsReceipt", "gr_id", "Read"))
):
    gr = db.query(models.GoodsReceipt).get(gr_id)
    if not gr:
        raise HTTPException(status_code=404, detail="GoodsReceipt not found")
    return gr

@router.post("/", response_model=schemas.GoodsReceipt)
@audit_log_change(action="CREATE", table_name="goods_receipt")
async def create_goods_receipt(
    gr: schemas.GoodsReceiptCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get parent PO to inherit owner_group_id
    po = db.get(models.PurchaseOrder, gr.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Parent purchase order not found")

    if current_user.role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create goods receipts")

    if current_user.role not in ["Admin", "Manager"]:
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [m.group_id for m in user_groups]

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

            if not po_access:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to create records under this parent. You must be in the owner group or have Write/Full access."
                )

    # Create GR with inherited owner_group_id (ignore client-provided value)
    db_gr = models.GoodsReceipt(
        **gr.model_dump(exclude={'owner_group_id'}),
        owner_group_id=po.owner_group_id,  # Inherit from parent
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_gr)
    db.commit()
    db.refresh(db_gr)
    return db_gr

@router.put("/{gr_id}", response_model=schemas.GoodsReceipt)
@audit_log_change(action="UPDATE", table_name="goods_receipt")
async def update_goods_receipt(
    gr_id: int,
    gr_update: schemas.GoodsReceiptUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("GoodsReceipt", "gr_id", "Write"))
):
    """Update an existing goods receipt."""
    gr = db.query(models.GoodsReceipt).get(gr_id)
    if not gr:
        raise HTTPException(status_code=404, detail="GoodsReceipt not found")

    # Apply updates (only provided fields)
    data = gr_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(gr, k, v)
    gr.updated_by = current_user.id
    gr.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(gr)
    return gr

@router.delete("/{gr_id}")
@audit_log_change(action="DELETE", table_name="goods_receipt")
async def delete_goods_receipt(
    gr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("GoodsReceipt", "gr_id", "Full"))
):
    gr = db.query(models.GoodsReceipt).get(gr_id)
    if not gr:
        raise HTTPException(status_code=404, detail="GoodsReceipt not found")
    db.delete(gr)
    db.commit()
    return {"status": "deleted", "id": gr_id}
