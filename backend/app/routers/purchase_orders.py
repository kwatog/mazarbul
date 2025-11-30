from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

@router.get("/", response_model=List[schemas.PurchaseOrder])
def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # TODO: Implement filtering based on user permissions/department if needed for list view
    # For now, returning all (Viewer+ sees all)
    return db.query(models.PurchaseOrder).all()

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
    current_user: models.User = Depends(get_current_user) # TODO: Check 'Create' permission generically?
):
    db_po = models.PurchaseOrder(
        **po.model_dump(),
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
