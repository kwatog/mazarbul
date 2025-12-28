from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import models, schemas
from ..database import SessionLocal
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/budget-items", tags=["budget-items"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.BudgetItem])
def list_budget_items(
    skip: int = 0,
    limit: int = 100,
    fiscal_year: int = None,
    owner_group_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all budget items with pagination and filtering."""
    query = db.query(models.BudgetItem)

    # Apply filters
    if fiscal_year:
        query = query.filter(models.BudgetItem.fiscal_year == fiscal_year)
    if owner_group_id:
        query = query.filter(models.BudgetItem.owner_group_id == owner_group_id)

    # Order by created_at descending
    query = query.order_by(models.BudgetItem.created_at.desc())

    # Apply pagination
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/{id}", response_model=schemas.BudgetItem)
def get_budget_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific budget item by ID."""
    budget_item = db.get(models.BudgetItem, id)
    if not budget_item:
        raise HTTPException(status_code=404, detail="Budget item not found")
    return budget_item


@router.post("/", response_model=schemas.BudgetItem)
def create_budget_item(
    budget_item: schemas.BudgetItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new budget item."""
    # Check if workday_ref already exists
    existing = db.query(models.BudgetItem).filter(
        models.BudgetItem.workday_ref == budget_item.workday_ref
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget item with this Workday reference already exists")

    # Create new budget item
    db_budget_item = models.BudgetItem(
        **budget_item.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )

    db.add(db_budget_item)

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="budget_item",
        record_id=db_budget_item.id,
        action="CREATE",
        new_values=budget_item.json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(db_budget_item)
    return db_budget_item


@router.put("/{id}", response_model=schemas.BudgetItem)
def update_budget_item(
    id: int,
    budget_item_update: schemas.BudgetItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an existing budget item."""
    db_budget_item = db.get(models.BudgetItem, id)
    if not db_budget_item:
        raise HTTPException(status_code=404, detail="Budget item not found")

    # Store old values for audit
    old_values = schemas.BudgetItem.from_orm(db_budget_item).dict()

    # Update fields
    update_data = budget_item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget_item, key, value)

    db_budget_item.updated_by = current_user.id
    db_budget_item.updated_at = datetime.utcnow().isoformat()

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="budget_item",
        record_id=id,
        action="UPDATE",
        old_values=schemas.BudgetItem(**old_values).json(),
        new_values=schemas.BudgetItem.from_orm(db_budget_item).json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(db_budget_item)
    return db_budget_item


@router.delete("/{id}")
def delete_budget_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    """Delete a budget item (Manager+ only)."""
    db_budget_item = db.get(models.BudgetItem, id)
    if not db_budget_item:
        raise HTTPException(status_code=404, detail="Budget item not found")

    # Check if budget item has associated line items
    line_items = db.query(models.BusinessCaseLineItem).filter(
        models.BusinessCaseLineItem.budget_item_id == id
    ).first()
    if line_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete budget item with associated business case line items"
        )

    # Store for audit
    old_values = schemas.BudgetItem.from_orm(db_budget_item).dict()

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="budget_item",
        record_id=id,
        action="DELETE",
        old_values=schemas.BudgetItem(**old_values).json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.delete(db_budget_item)
    db.commit()

    return {"message": "Budget item deleted successfully"}
