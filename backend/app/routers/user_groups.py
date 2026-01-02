from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
from ..auth import get_db, get_current_user, require_role

router = APIRouter(prefix="/user-groups", tags=["user-groups"])

@router.get("/", response_model=List[schemas.UserGroup])
def list_groups(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.UserGroup).all()

@router.post("/", response_model=schemas.UserGroup)
def create_group(
    group: schemas.UserGroupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    db_group = models.UserGroup(
        **group.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/{group_id}", response_model=schemas.UserGroup)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = db.query(models.UserGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.put("/{group_id}", response_model=schemas.UserGroup)
def update_group(
    group_id: int,
    group_update: schemas.UserGroupUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    group = db.query(models.UserGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    data = group_update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(group, k, v)
    
    db.commit()
    db.refresh(group)
    return group

@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    group = db.query(models.UserGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(group)
    db.commit()
    return {"status": "deleted", "id": group_id}

@router.get("/{group_id}/members", response_model=List[schemas.UserGroupMembership])
def list_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.UserGroupMembership).filter(models.UserGroupMembership.group_id == group_id).all()

@router.post("/{group_id}/members", response_model=schemas.UserGroupMembership)
def add_group_member(
    group_id: int,
    membership: schemas.UserGroupMembershipCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    if membership.group_id != group_id:
        raise HTTPException(status_code=400, detail="Group ID mismatch")
        
    db_member = models.UserGroupMembership(
        **membership.model_dump(),
        added_by=current_user.id,
        added_at=datetime.utcnow().isoformat()
    )
    try:
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="User likely already in group")
    return db_member

@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("Manager"))
):
    membership = db.query(models.UserGroupMembership).filter(
        models.UserGroupMembership.group_id == group_id,
        models.UserGroupMembership.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
        
    db.delete(membership)
    db.commit()
    return {"status": "deleted"}
