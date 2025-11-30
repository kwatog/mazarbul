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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.GoodsReceipt).all()

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
    db_gr = models.GoodsReceipt(
        **gr.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_gr)
    db.commit()
    db.refresh(db_gr)
    return db_gr

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
