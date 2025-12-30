from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import models, schemas
from ..database import SessionLocal
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/business-case-line-items", tags=["business-case-line-items"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.BusinessCaseLineItem])
def list_line_items(
    skip: int = 0,
    limit: int = 100,
    business_case_id: int = None,
    owner_group_id: int = None,
    spend_category: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all business case line items with pagination and filtering."""
    query = db.query(models.BusinessCaseLineItem)

    # CRITICAL: Filter by owner_group_id access (only show records user can access)
    if current_user.role not in ["Admin", "Manager"]:
        # Get all groups the user is a member of
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        group_ids = [membership.group_id for membership in user_groups]

        # Filter to accessible records
        accessible_ids_query = db.query(models.BusinessCaseLineItem.id).filter(
            (models.BusinessCaseLineItem.owner_group_id.in_(group_ids)) |
            (models.BusinessCaseLineItem.created_by == current_user.id)
        )

        # Add explicit RecordAccess grants
        explicit_access = db.query(models.RecordAccess.record_id).filter(
            models.RecordAccess.record_type == "BusinessCaseLineItem",
            models.RecordAccess.user_id == current_user.id,
            (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
        )

        accessible_ids = [item.id for item in accessible_ids_query.all()]
        accessible_ids += [access.record_id for access in explicit_access.all()]

        query = query.filter(models.BusinessCaseLineItem.id.in_(accessible_ids))

    # Apply filters
    if business_case_id:
        query = query.filter(models.BusinessCaseLineItem.business_case_id == business_case_id)
    if owner_group_id:
        query = query.filter(models.BusinessCaseLineItem.owner_group_id == owner_group_id)
    if spend_category:
        query = query.filter(models.BusinessCaseLineItem.spend_category == spend_category)

    # Order by created_at descending
    query = query.order_by(models.BusinessCaseLineItem.created_at.desc())

    # Apply pagination
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/{id}", response_model=schemas.BusinessCaseLineItem)
def get_line_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific business case line item by ID."""
    line_item = db.get(models.BusinessCaseLineItem, id)
    if not line_item:
        raise HTTPException(status_code=404, detail="Business case line item not found")
    return line_item


@router.post("/", response_model=schemas.BusinessCaseLineItem)
def create_line_item(
    line_item: schemas.BusinessCaseLineItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new business case line item."""
    # Verify business case exists
    business_case = db.get(models.BusinessCase, line_item.business_case_id)
    if not business_case:
        raise HTTPException(status_code=404, detail="Business case not found")

    # Verify budget item exists
    budget_item = db.get(models.BudgetItem, line_item.budget_item_id)
    if not budget_item:
        raise HTTPException(status_code=404, detail="Budget item not found")

    # Create new line item
    db_line_item = models.BusinessCaseLineItem(
        **line_item.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )

    db.add(db_line_item)

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="business_case_line_item",
        record_id=db_line_item.id,
        action="CREATE",
        new_values=line_item.json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(db_line_item)
    return db_line_item


@router.put("/{id}", response_model=schemas.BusinessCaseLineItem)
def update_line_item(
    id: int,
    line_item_update: schemas.BusinessCaseLineItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an existing business case line item."""
    db_line_item = db.get(models.BusinessCaseLineItem, id)
    if not db_line_item:
        raise HTTPException(status_code=404, detail="Business case line item not found")

    # Store old values for audit
    old_values = schemas.BusinessCaseLineItem.from_orm(db_line_item).dict()

    # Update fields
    update_data = line_item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_line_item, key, value)

    db_line_item.updated_by = current_user.id
    db_line_item.updated_at = datetime.utcnow().isoformat()

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="business_case_line_item",
        record_id=id,
        action="UPDATE",
        old_values=schemas.BusinessCaseLineItem(**old_values).json(),
        new_values=schemas.BusinessCaseLineItem.from_orm(db_line_item).json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(db_line_item)
    return db_line_item


@router.delete("/{id}")
def delete_line_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    """Delete a business case line item (Manager+ only)."""
    db_line_item = db.get(models.BusinessCaseLineItem, id)
    if not db_line_item:
        raise HTTPException(status_code=404, detail="Business case line item not found")

    # Check if line item has associated WBS items
    wbs_items = db.query(models.WBS).filter(
        models.WBS.business_case_line_item_id == id
    ).first()
    if wbs_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete line item with associated WBS items"
        )

    # Store for audit
    old_values = schemas.BusinessCaseLineItem.from_orm(db_line_item).dict()

    # Add audit log
    audit_entry = models.AuditLog(
        table_name="business_case_line_item",
        record_id=id,
        action="DELETE",
        old_values=schemas.BusinessCaseLineItem(**old_values).json(),
        user_id=current_user.id,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(audit_entry)

    db.delete(db_line_item)
    db.commit()

    return {"message": "Business case line item deleted successfully"}
