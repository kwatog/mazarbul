from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import SessionLocal
from .. import models
from ..auth import get_db, get_current_user, now_utc

router = APIRouter(prefix="/alerts", tags=["alerts"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    """Get all group IDs the user belongs to."""
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def can_user_access_record(db: Session, user: models.User, record_type: str, record_id: int, owner_group_id: int) -> bool:
    """Check if user can access a specific record."""
    if user.role in ["Admin", "Manager"]:
        return True
    
    user_group_ids = get_user_group_ids(db, user.id)
    
    if owner_group_id in user_group_ids:
        return True
    
    if record_type == "PurchaseOrder":
        record = db.get(models.PurchaseOrder, record_id)
    elif record_type == "Resource":
        record = db.get(models.Resource, record_id)
    else:
        return False
    
    if record and record.created_by == user.id:
        return True
    
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == record_type,
        models.RecordAccess.record_id == record_id,
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
    ).first()
    
    if user_access:
        return True
    
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == record_type,
        models.RecordAccess.record_id == record_id,
        models.RecordAccess.group_id.in_(user_group_ids) if user_group_ids else False,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > now_utc())
    ).first()
    
    if group_access:
        return True
    
    return False

@router.get("/", response_model=List[Dict[str, Any]])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alerts = []
    today = datetime.now().date()
    current_month = datetime.now().month
    current_year = datetime.now().year

    pos = db.query(models.PurchaseOrder).all()
    
    for po in pos:
        if not can_user_access_record(db, current_user, "PurchaseOrder", po.id, po.owner_group_id):
            continue
        
        total_gr = sum(gr.amount for gr in po.goods_receipts)
        remaining = po.total_amount - total_gr
        
        threshold = po.total_amount * Decimal("0.10")
        if remaining < threshold and po.status == "Open":
            alerts.append({
                "type": "low_po_balance",
                "message": f"PO {po.po_number} has low balance ({remaining} remaining)",
                "severity": "warning",
                "entity_id": po.id,
                "entity_type": "purchase_order"
            })

        if po.status == "Open":
            has_gr_this_month = any(gr.gr_date and gr.gr_date.month == current_month and gr.gr_date.year == current_year for gr in po.goods_receipts)
            if not has_gr_this_month:
                alerts.append({
                    "type": "no_gr_this_month",
                    "message": f"PO {po.po_number} has no Goods Receipt for this month ({current_year}-{current_month:02d})",
                    "severity": "info",
                    "entity_id": po.id,
                    "entity_type": "purchase_order"
                })
        
        if not po.asset:
            alerts.append({
                "type": "missing_chain",
                "message": f"PO {po.po_number} is missing an Asset",
                "severity": "error",
                "entity_id": po.id,
                "entity_type": "purchase_order"
            })
        elif not po.asset.wbs:
            alerts.append({
                 "type": "missing_chain",
                 "message": f"Asset {po.asset.asset_code} (linked to PO {po.po_number}) is missing a WBS",
                 "severity": "error",
                 "entity_id": po.asset.id,
                 "entity_type": "asset"
            })
        elif not po.asset.wbs.business_case:
             alerts.append({
                 "type": "missing_chain",
                 "message": f"WBS {po.asset.wbs.wbs_code} (linked to PO {po.po_number}) is missing a Business Case",
                 "severity": "error",
                 "entity_id": po.asset.wbs.id,
                 "entity_type": "wbs"
             })

    resources = db.query(models.Resource).filter(models.Resource.status == "Active").all()
    
    for res in resources:
        if not can_user_access_record(db, current_user, "Resource", res.id, res.owner_group_id):
            continue
        
        has_active_allocation = False
        for alloc in res.allocations:
            if alloc.allocation_start and alloc.allocation_end:
                if alloc.allocation_start.date() <= today <= alloc.allocation_end.date():
                    has_active_allocation = True
                    break

        if not has_active_allocation:
            alerts.append({
                "type": "resource_without_po",
                "message": f"Resource {res.name} is Active but has no PO allocation for today ({today})",
                "severity": "warning",
                "entity_id": res.id,
                "entity_type": "resource"
            })

    return alerts
