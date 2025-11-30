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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.BusinessCase).all()

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
