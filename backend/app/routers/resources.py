from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/resources", tags=["resources"])

@router.get("/", response_model=List[schemas.Resource])
def list_resources(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Resource).all()

@router.get("/{resource_id}", response_model=schemas.Resource)
def get_resource(
    resource_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Resource", "resource_id", "Read"))
):
    resource = db.query(models.Resource).get(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@router.post("/", response_model=schemas.Resource)
@audit_log_change(action="CREATE", table_name="resource")
async def create_resource(
    resource: schemas.ResourceCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_resource = models.Resource(
        **resource.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@router.delete("/{resource_id}")
@audit_log_change(action="DELETE", table_name="resource")
async def delete_resource(
    resource_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Resource", "resource_id", "Full"))
):
    resource = db.query(models.Resource).get(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()
    return {"status": "deleted", "id": resource_id}
