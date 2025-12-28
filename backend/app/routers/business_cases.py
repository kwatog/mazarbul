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
    """List all business cases with pagination and filtering."""
    query = db.query(models.BusinessCase)

    # Apply filters
    if status:
        query = query.filter(models.BusinessCase.status == status)
    if requestor:
        query = query.filter(models.BusinessCase.requestor.ilike(f"%{requestor}%"))

    # Order by created_at descending
    query = query.order_by(models.BusinessCase.created_at.desc())

    # Apply pagination
    return query.offset(skip).limit(limit).all()

@router.get("/{bc_id}", response_model=schemas.BusinessCase)
def get_business_case(
    bc_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("BusinessCase", "bc_id", "Read"))
):
    bc = db.query(models.BusinessCase).get(bc_id)
    if not bc:
        raise HTTPException(status_code=404, detail="BusinessCase not found")
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

@router.delete("/{bc_id}")
@audit_log_change(action="DELETE", table_name="business_case")
async def delete_business_case(
    bc_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("BusinessCase", "bc_id", "Full"))
):
    bc = db.query(models.BusinessCase).get(bc_id)
    if not bc:
        raise HTTPException(status_code=404, detail="BusinessCase not found")
    db.delete(bc)
    db.commit()
    return {"status": "deleted", "id": bc_id}
