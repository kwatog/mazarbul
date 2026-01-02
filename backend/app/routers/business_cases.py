from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/business-cases", tags=["business-cases"])

@router.get("/", response_model=List[schemas.BusinessCase])
def list_business_cases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    requestor: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all business cases with pagination and filtering - implements hybrid access control."""
    from app.auth import check_business_case_access

    query = db.query(models.BusinessCase)

    # Apply filters
    if status:
        query = query.filter(models.BusinessCase.status == status)
    if requestor:
        query = query.filter(models.BusinessCase.requestor.ilike(f"%{requestor}%"))

    # Order by created_at descending
    query = query.order_by(models.BusinessCase.created_at.desc())

    # Get all BCs and filter by hybrid access control
    all_bcs = query.all()

    # CRITICAL: Filter by hybrid access control (creator + line-item + explicit)
    if current_user.role not in ["Admin", "Manager"]:
        accessible_bcs = []
        for bc in all_bcs:
            if check_business_case_access(current_user, bc, db, "Read"):
                accessible_bcs.append(bc)
        # Apply pagination to filtered results
        return accessible_bcs[skip:skip+limit]

    # Admin/Manager see all - apply pagination
    return all_bcs[skip:skip+limit]

@router.get("/{bc_id}", response_model=schemas.BusinessCase)
def get_business_case(
    bc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific business case - uses hybrid access control."""
    from app.auth import check_business_case_access

    bc = db.query(models.BusinessCase).get(bc_id)
    if not bc:
        raise HTTPException(status_code=404, detail="BusinessCase not found")

    # CRITICAL: Check hybrid access control
    if current_user.role not in ["Admin", "Manager"]:
        if not check_business_case_access(current_user, bc, db, "Read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions to access this business case")

    return bc

@router.post("/", response_model=schemas.BusinessCase)
@audit_log_change(action="CREATE", table_name="business_case")
async def create_business_case(
    bc: schemas.BusinessCaseCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_bc = models.BusinessCase(
        **bc.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_bc)
    db.commit()
    db.refresh(db_bc)
    return db_bc

@router.put("/{bc_id}", response_model=schemas.BusinessCase)
async def update_business_case(
    bc_id: int,
    bc_update: schemas.BusinessCaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a business case with validation for status transitions."""
    from app.auth import check_business_case_access

    # Fetch the business case
    bc = db.query(models.BusinessCase).get(bc_id)
    if not bc:
        raise HTTPException(status_code=404, detail="BusinessCase not found")

    # Check access using hybrid access control
    if current_user.role not in ["Admin", "Manager"]:
        if not check_business_case_access(current_user, bc, db, "Write"):
            raise HTTPException(status_code=403, detail="Insufficient permissions to update this business case")

    # CRITICAL: Validate status transition from Draft requires ≥1 line item
    if bc_update.status and bc_update.status != "Draft" and bc.status == "Draft":
        line_item_count = db.query(models.BusinessCaseLineItem).filter(
            models.BusinessCaseLineItem.business_case_id == bc_id
        ).count()

        if line_item_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot transition from Draft status without at least one line item"
            )

    # Update fields
    for field, value in bc_update.model_dump(exclude_unset=True).items():
        setattr(bc, field, value)

    bc.updated_by = current_user.id
    bc.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(bc)
    return bc

@router.delete("/{bc_id}")
@audit_log_change(action="DELETE", table_name="business_case")
async def delete_business_case(
    bc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a business case - uses hybrid access control."""
    bc = db.query(models.BusinessCase).get(bc_id)
    if not bc:
        raise HTTPException(status_code=404, detail="BusinessCase not found")

    if current_user.role not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin/Manager can delete a business case"
        )

    db.delete(bc)
    db.commit()
    return {"status": "deleted", "id": bc_id}
