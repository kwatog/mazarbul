from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/goods-receipts", tags=["goods-receipts"])

@router.get("/", response_model=List[schemas.GoodsReceipt])
def list_goods_receipts(
    skip: int = 0,
    limit: int = 100,
    po_id: int = None,
    owner_group_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all goods receipts with pagination and filtering."""
    query = db.query(models.GoodsReceipt)

    # Apply filters
    if po_id:
        query = query.filter(models.GoodsReceipt.po_id == po_id)
    if owner_group_id:
        query = query.filter(models.GoodsReceipt.owner_group_id == owner_group_id)

    # Order by gr_date descending
    query = query.order_by(models.GoodsReceipt.gr_date.desc())

    # Apply pagination
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
