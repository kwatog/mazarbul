from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from ..database import SessionLocal
from .. import models
from ..auth import get_db, get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Alerts logic doesn't write, so simpler
    alerts = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_month = datetime.now().strftime("%Y-%m")

    # 1. Low PO balance & 2. No GR this month
    # Get all POs
    pos = db.query(models.PurchaseOrder).all()
    
    for po in pos:
        # Logic for Low PO Balance
        total_gr = sum(gr.amount for gr in po.goods_receipts)
        remaining = po.total_amount - total_gr
        
        # Threshold: hardcoded 10% for now as per spec suggestion "threshold configurable"
        threshold = po.total_amount * 0.10
        if remaining < threshold and po.status == "Open":
            alerts.append({
                "type": "low_po_balance",
                "message": f"PO {po.po_number} has low balance ({remaining} remaining)",
                "severity": "warning",
                "entity_id": po.id,
                "entity_type": "purchase_order"
            })

        # Logic for No GR this month
        if po.status == "Open":
            has_gr_this_month = any(gr.gr_date and gr.gr_date.startswith(current_month) for gr in po.goods_receipts)
            if not has_gr_this_month:
                alerts.append({
                    "type": "no_gr_this_month",
                    "message": f"PO {po.po_number} has no Goods Receipt for this month ({current_month})",
                    "severity": "info",
                    "entity_id": po.id,
                    "entity_type": "purchase_order"
                })
        
        # Logic for Missing chain
        # PO -> Asset -> WBS -> BusinessCase
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

    # 3. Resource without PO
    # Resource has status = 'Active' AND no allocation covering today
    resources = db.query(models.Resource).filter(models.Resource.status == "Active").all()
    
    for res in resources:
        has_active_allocation = False
        for alloc in res.allocations:
            if alloc.allocation_start and alloc.allocation_end:
                if alloc.allocation_start <= today_str <= alloc.allocation_end:
                    has_active_allocation = True
                    break
        
        if not has_active_allocation:
            alerts.append({
                "type": "resource_without_po",
                "message": f"Resource {res.name} is Active but has no PO allocation for today ({today_str})",
                "severity": "warning",
                "entity_id": res.id,
                "entity_type": "resource"
            })

    return alerts
