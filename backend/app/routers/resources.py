from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, check_record_access, audit_log_change

router = APIRouter(prefix="/resources", tags=["resources"])

def get_user_group_ids(db: Session, user_id: int) -> List[int]:
    memberships = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.user_id == user_id
    ).all()
    return [m.group_id for m in memberships]

def get_accessible_resource_ids(db: Session, user: models.User) -> List[int]:
    if user.role in ["Admin", "Manager"]:
        all_resources = db.query(models.Resource.id).all()
        return [r[0] for r in all_resources]
    
    user_group_ids = get_user_group_ids(db, user.id)
    
    owned_resources = db.query(models.Resource.id).filter(
        models.Resource.owner_group_id.in_(user_group_ids)
    ).all()
    owned_ids = [r[0] for r in owned_resources]
    
    created_resources = db.query(models.Resource.id).filter(
        models.Resource.created_by == user.id
    ).all()
    created_ids = [r[0] for r in created_resources]
    
    user_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "Resource",
        models.RecordAccess.user_id == user.id,
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    group_access = db.query(models.RecordAccess).filter(
        models.RecordAccess.record_type == "Resource",
        models.RecordAccess.group_id.in_(user_group_ids),
        (models.RecordAccess.expires_at.is_(None)) | (models.RecordAccess.expires_at > datetime.utcnow().isoformat())
    ).all()
    
    accessible_ids = set(owned_ids + created_ids)
    for access in user_access + group_access:
        accessible_ids.add(access.record_id)
    
    return list(accessible_ids)

@router.get("/", response_model=List[schemas.Resource])
def list_resources(
    skip: int = 0,
    limit: int = 100,
    owner_group_id: Optional[int] = None,
    status: Optional[str] = None,
    vendor: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all resources with pagination and filtering.
    
    For non-admin users, only returns resources they can access via:
    - Owner-group membership
    - Explicit RecordAccess grants
    - Records they created
    """
    accessible_ids = get_accessible_resource_ids(db, current_user)
    
    query = db.query(models.Resource).filter(models.Resource.id.in_(accessible_ids))

    if owner_group_id is not None:
        query = query.filter(models.Resource.owner_group_id == owner_group_id)
    if status is not None:
        query = query.filter(models.Resource.status == status)
    if vendor is not None:
        query = query.filter(models.Resource.vendor.ilike(f"%{vendor}%"))

    query = query.order_by(models.Resource.created_at.desc())

    return query.offset(skip).limit(limit).all()

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

@router.put("/{resource_id}", response_model=schemas.Resource)
@audit_log_change(action="UPDATE", table_name="resource")
async def update_resource(
    resource_id: int,
    resource_update: schemas.ResourceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_record_access("Resource", "resource_id", "Write"))
):
    """Update an existing resource."""
    resource = db.query(models.Resource).get(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    data = resource_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(resource, k, v)
    resource.updated_by = current_user.id
    resource.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(resource)
    return resource

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
