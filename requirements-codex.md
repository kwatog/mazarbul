# Mazarbul – Codex Master Spec

> Feed this whole file to a code LLM and say:  
> **"Read through requirements-codex.md and generate the codebase for me."**

---

## 0. Project Overview

**Name:** Mazarbul  
**Domain:** Procurement & Resource Tracking  

**Goal:** Replace Excel-based tracking of:
- Business Case → WBS → Asset → SOW (future) → Purchase Order → Goods Receipt
- Resource ↔ Purchase Order allocation
- PO burn / remaining amount
- Alerts when POs are running out or data is missing

**Stack:**
- Frontend: Nuxt 4 (Vue 3, TypeScript allowed)
- Backend: FastAPI (Python)
- Database: SQLite (file-based, foreign keys ON)

---

## 1. Data Model (Entities)

### 1.1 User
- id: int PK
- username: string UNIQUE
- email: string UNIQUE  
- hashed_password: string
- full_name: string
- department: string
- role: string (Admin, Manager, User, Viewer)
- is_active: bool (default True)
- created_at: string (ISO datetime)
- last_login: string (ISO datetime, nullable)

### 1.2 BusinessCase
- id: int PK  
- title: text  
- description: text  
- requestor: text  
- dept: text  
- estimated_cost: float  
- created_at: string (ISO date or datetime)  
- status: string (Draft, Submitted, Approved, Rejected, etc.)
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- updated_at: string (ISO datetime, audit)

### 1.3 WBS
- id: int PK  
- business_case_id: int FK → BusinessCase.id  
- wbs_code: string UNIQUE  
- description: text  
- status: string
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)  

### 1.4 Asset
- id: int PK  
- wbs_id: int FK → WBS.id  
- asset_code: string UNIQUE  
- asset_type: string (Capex, Opex)  
- description: text  
- status: string
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)  

### 1.5 PurchaseOrder
- id: int PK  
- asset_id: int FK → Asset.id  
- po_number: string UNIQUE  
- supplier: string  
- po_type: string (T&M, Fixed, etc.)  
- start_date: string  
- end_date: string  
- total_amount: float  
- currency: string  
- status: string (Open, Closed, Exhausted, etc.)
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)

### 1.6 GoodsReceipt
- id: int PK  
- po_id: int FK → PurchaseOrder.id  
- gr_number: string UNIQUE  
- gr_date: string  
- amount: float  
- description: text
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)  

### 1.7 Resource
- id: int PK  
- name: string  
- vendor: string  
- role: string  
- start_date: string  
- end_date: string  
- cost_per_month: float  
- status: string (Active, Inactive, Left, etc.)
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)

### 1.8 ResourcePOAllocation
- id: int PK  
- resource_id: int FK → Resource.id  
- po_id: int FK → PurchaseOrder.id  
- allocation_start: string  
- allocation_end: string  
- expected_monthly_burn: float
- created_by: int FK → User.id (audit)
- updated_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)
- updated_at: string (ISO datetime, audit)  

### 1.9 UserGroup
- id: int PK
- name: string UNIQUE
- description: text
- created_by: int FK → User.id (audit)
- created_at: string (ISO datetime, audit)

### 1.10 UserGroupMembership
- id: int PK
- user_id: int FK → User.id
- group_id: int FK → UserGroup.id
- added_by: int FK → User.id (audit)
- added_at: string (ISO datetime, audit)

### 1.11 RecordAccess
- id: int PK
- record_type: string (BusinessCase, WBS, Asset, PurchaseOrder, GoodsReceipt, Resource, ResourcePOAllocation)
- record_id: int (the ID of the specific record)
- user_id: int FK → User.id (nullable - for individual user access)
- group_id: int FK → UserGroup.id (nullable - for group access)
- access_level: string (Read, Write, Full)
- granted_by: int FK → User.id (who granted this access)
- granted_at: string (ISO datetime)
- expires_at: string (ISO datetime, nullable)

### 1.12 AuditLog
- id: int PK
- table_name: string (which table was affected)
- record_id: int (which record was affected)
- action: string (CREATE, UPDATE, DELETE)
- old_values: text (JSON of old values, null for CREATE)
- new_values: text (JSON of new values, null for DELETE)  
- user_id: int FK → User.id (who performed the action)
- timestamp: string (ISO datetime)
- ip_address: string (nullable)
- user_agent: string (nullable)

---

## 2. Behaviors & Business Logic

### 2.1 PO Remaining Amount

For a given PurchaseOrder:

```text
remaining = purchase_order.total_amount
          - SUM(all goods_receipt.amount for that PO)
```

If no GRs exist, remaining = total_amount.

### 2.2 Alerts

Alerts are computed on request (no need to persist initially).

Alert types:

1. **Low PO balance**  
   - Condition: `remaining < threshold` (threshold configurable; % of total or fixed amount).

2. **No GR this month**  
   - Condition: PO has `status = 'Open'`  
   - AND there is no `GoodsReceipt` for that `po_id` with `gr_date` in current month.

3. **Resource without PO**  
   - Condition: Resource has `status = 'Active'`  
   - AND there is no `ResourcePOAllocation` such that  
     `allocation_start <= today <= allocation_end`.

4. **Missing chain**  
   - Condition: For a given PurchaseOrder:  
     - missing Asset, OR  
     - Asset missing WBS, OR  
     - WBS missing BusinessCase.

Expose alerts via `GET /alerts`.

### 2.3 Record-Level Access Control

**Default Access:**
- Creator of a record has Full access by default
- Users with Manager/Admin roles have access based on role permissions
- Department-based access still applies for User role

**Access Levels:**
- **Read**: View record and its data
- **Write**: Read + Edit record data 
- **Full**: Write + Delete record + Grant access to others

**Access Resolution Logic:**
For any record access request:
1. Check if user is Admin → Full access to all records
2. Check if user is Manager → Full access to all records  
3. Check if user is creator → Full access
4. Check explicit RecordAccess grants for user → use highest access level
5. Check RecordAccess grants for user's groups → use highest access level
6. Check department-based access (User role) → department records only
7. Deny access

**Inheritance Rules:**
- Child records inherit access from parent where logical:
  - WBS inherits from BusinessCase
  - Asset inherits from WBS  
  - PurchaseOrder inherits from Asset
  - GoodsReceipt inherits from PurchaseOrder
  - ResourcePOAllocation inherits from both Resource and PurchaseOrder (intersection)

### 2.4 Audit Trail

All create/update/delete operations must:
1. Record the user performing the action (created_by/updated_by)
2. Record the timestamp (created_at/updated_at)  
3. Log the action in audit trail (see AuditLog entity below)

---

## 3. Authentication & Authorization

### 3.1 Authentication System

**JWT Token-based Authentication:**
- Use JWT tokens for stateless authentication
- Access token expires in 15 minutes
- Refresh token expires in 7 days
- Store tokens in HTTP-only cookies for security

### 3.2 Password Security
- Hash passwords using bcrypt with salt rounds >= 12
- Enforce minimum password requirements:
  - At least 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter  
  - At least 1 number
  - At least 1 special character

### 3.3 User Roles & Permissions

**Role Hierarchy:**
1. **Viewer** - Read-only access to all entities
2. **User** - Create/Edit own department's data + Viewer permissions
3. **Manager** - Create/Edit/Delete all data + User permissions  
4. **Admin** - User management + Manager permissions

**Permission Matrix:**
```
Entity          | Viewer | User | Manager | Admin
----------------|--------|------|---------|-------
Users           | Read   | Read | Read    | Full
UserGroups      | Read   | Read | Full    | Full
BusinessCase    | Read** | CRUD*| Full    | Full
WBS             | Read** | CRUD*| Full    | Full
Asset           | Read** | CRUD*| Full    | Full
PurchaseOrder   | Read** | CRUD*| Full    | Full
GoodsReceipt    | Read** | CRUD*| Full    | Full
Resource        | Read** | CRUD*| Full    | Full
Allocation      | Read** | CRUD*| Full    | Full
RecordAccess    | Read   | Grant+| Full    | Full
AuditLog        | Read   | Read | Read    | Full
Alerts          | Read   | Read | Read    | Read

* CRUD only for own department's data + granted record access
** Subject to record-level access control
+ Grant access only to own created records
```

### 3.4 Authentication & Access Management Endpoints

```
# Authentication
POST /auth/register     - Register new user (Admin only)
POST /auth/login        - Login with username/password
POST /auth/logout       - Logout (invalidate tokens)
POST /auth/refresh      - Refresh access token
GET  /auth/me          - Get current user info
PUT  /auth/me          - Update current user profile
PUT  /auth/password    - Change password

# User Groups
GET  /user-groups              - List all user groups
POST /user-groups              - Create new user group (Manager+)
GET  /user-groups/{id}         - Get user group details
PUT  /user-groups/{id}         - Update user group (Manager+)
DELETE /user-groups/{id}       - Delete user group (Manager+)
POST /user-groups/{id}/members - Add user to group (Manager+)
DELETE /user-groups/{id}/members/{user_id} - Remove user from group (Manager+)

# Record Access Management
GET  /record-access/{record_type}/{record_id}     - Get access list for record
POST /record-access/{record_type}/{record_id}     - Grant access to record
PUT  /record-access/{id}                          - Update access grant
DELETE /record-access/{id}                        - Revoke access grant

# Audit Trail
GET  /audit-logs                                  - Get audit logs (filterable)
GET  /audit-logs/{record_type}/{record_id}        - Get audit logs for specific record
```

### 3.5 Route Protection

All API routes except `/health` and `/auth/login` require authentication.
Use dependency injection to check:
1. Valid JWT token
2. User permissions for the requested operation
3. Department-based data access control

### 3.6 Frontend Authentication

**Login Flow:**
1. User submits credentials to `/auth/login`
2. Backend validates and returns JWT tokens in HTTP-only cookies
3. Frontend redirects to dashboard
4. All API calls automatically include cookies
5. Handle token refresh automatically on 401 responses

**Route Guards:**
- Redirect unauthenticated users to `/login`
- Show/hide UI elements based on user role
- Protect admin routes from non-admin users

---

## 4. Database Schema (SQLite)

### 4.1 SQL Schema

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  full_name TEXT NOT NULL,
  department TEXT,
  role TEXT DEFAULT 'User',
  is_active BOOLEAN DEFAULT 1,
  created_at TEXT,
  last_login TEXT
);

CREATE TABLE IF NOT EXISTS business_case (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  requestor TEXT,
  dept TEXT,
  estimated_cost REAL,
  created_at TEXT,
  status TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  updated_at TEXT,
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS wbs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  business_case_id INTEGER,
  wbs_code TEXT UNIQUE,
  description TEXT,
  status TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (business_case_id) REFERENCES business_case(id),
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS asset (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wbs_id INTEGER,
  asset_code TEXT UNIQUE,
  asset_type TEXT,
  description TEXT,
  status TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (wbs_id) REFERENCES wbs(id),
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS purchase_order (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER,
  po_number TEXT UNIQUE,
  supplier TEXT,
  po_type TEXT,
  start_date TEXT,
  end_date TEXT,
  total_amount REAL,
  currency TEXT,
  status TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (asset_id) REFERENCES asset(id),
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS goods_receipt (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  po_id INTEGER,
  gr_number TEXT UNIQUE,
  gr_date TEXT,
  amount REAL,
  description TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (po_id) REFERENCES purchase_order(id),
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS resource (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  vendor TEXT,
  role TEXT,
  start_date TEXT,
  end_date TEXT,
  cost_per_month REAL,
  status TEXT,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS resource_po_allocation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resource_id INTEGER,
  po_id INTEGER,
  allocation_start TEXT,
  allocation_end TEXT,
  expected_monthly_burn REAL,
  created_by INTEGER,
  updated_by INTEGER,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (resource_id) REFERENCES resource(id),
  FOREIGN KEY (po_id) REFERENCES purchase_order(id),
  FOREIGN KEY (created_by) REFERENCES user(id),
  FOREIGN KEY (updated_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS user_group (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_by INTEGER,
  created_at TEXT,
  FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS user_group_membership (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  group_id INTEGER,
  added_by INTEGER,
  added_at TEXT,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (group_id) REFERENCES user_group(id),
  FOREIGN KEY (added_by) REFERENCES user(id),
  UNIQUE(user_id, group_id)
);

CREATE TABLE IF NOT EXISTS record_access (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_type TEXT NOT NULL,
  record_id INTEGER NOT NULL,
  user_id INTEGER,
  group_id INTEGER,
  access_level TEXT NOT NULL,
  granted_by INTEGER,
  granted_at TEXT,
  expires_at TEXT,
  FOREIGN KEY (user_id) REFERENCES user(id),
  FOREIGN KEY (group_id) REFERENCES user_group(id),
  FOREIGN KEY (granted_by) REFERENCES user(id),
  CHECK (user_id IS NOT NULL OR group_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name TEXT NOT NULL,
  record_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  old_values TEXT,
  new_values TEXT,
  user_id INTEGER,
  timestamp TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## 5. Backend – FastAPI + SQLAlchemy

### 5.1 Database Setup (`backend/app/database.py`)

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///../mazarbul.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

@event.listens_for(engine, "connect")
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### 5.2 SQLAlchemy Models (`backend/app/models.py`)

```python
from sqlalchemy import Column, Integer, String, Text, Real, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class BusinessCase(Base):
    __tablename__ = "business_case"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    requestor = Column(String(255))
    dept = Column(String(255))
    estimated_cost = Column(Real)
    created_at = Column(String(32))
    status = Column(String(50))

    wbs_items = relationship("WBS", back_populates="business_case")


class WBS(Base):
    __tablename__ = "wbs"

    id = Column(Integer, primary_key=True, index=True)
    business_case_id = Column(Integer, ForeignKey("business_case.id"))
    wbs_code = Column(String(255), unique=True)
    description = Column(Text)
    status = Column(String(50))

    business_case = relationship("BusinessCase", back_populates="wbs_items")
    assets = relationship("Asset", back_populates="wbs")


class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, index=True)
    wbs_id = Column(Integer, ForeignKey("wbs.id"))
    asset_code = Column(String(255), unique=True)
    asset_type = Column(String(50))
    description = Column(Text)
    status = Column(String(50))

    wbs = relationship("WBS", back_populates="assets")
    purchase_orders = relationship("PurchaseOrder", back_populates="asset")


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id"))
    po_number = Column(String(255), unique=True, index=True)
    supplier = Column(String(255))
    po_type = Column(String(50))
    start_date = Column(String(32))
    end_date = Column(String(32))
    total_amount = Column(Real)
    currency = Column(String(10))
    status = Column(String(50))

    asset = relationship("Asset", back_populates="purchase_orders")
    goods_receipts = relationship("GoodsReceipt", back_populates="po")
    allocations = relationship("ResourcePOAllocation", back_populates="po")


class GoodsReceipt(Base):
    __tablename__ = "goods_receipt"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_order.id"))
    gr_number = Column(String(255), unique=True, index=True)
    gr_date = Column(String(32))
    amount = Column(Real)
    description = Column(Text)

    po = relationship("PurchaseOrder", back_populates="goods_receipts")


class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    vendor = Column(String(255))
    role = Column(String(255))
    start_date = Column(String(32))
    end_date = Column(String(32))
    cost_per_month = Column(Real)
    status = Column(String(50))

    allocations = relationship("ResourcePOAllocation", back_populates="resource")


class ResourcePOAllocation(Base):
    __tablename__ = "resource_po_allocation"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resource.id"))
    po_id = Column(Integer, ForeignKey("purchase_order.id"))
    allocation_start = Column(String(32))
    allocation_end = Column(String(32))
    expected_monthly_burn = Column(Real)

    resource = relationship("Resource", back_populates="allocations")
    po = relationship("PurchaseOrder", back_populates="allocations")
```

### 5.3 Pydantic Schemas Example (`backend/app/schemas.py` – PurchaseOrder)

```python
from pydantic import BaseModel
from typing import Optional


class PurchaseOrderBase(BaseModel):
    asset_id: int
    po_number: str
    supplier: Optional[str] = None
    po_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_amount: float
    currency: str
    status: Optional[str] = "Open"


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrder(PurchaseOrderBase):
    id: int

    class Config:
        orm_mode = True
```

### 5.4 Main App (`backend/app/main.py`)

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from . import models, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mazarbul API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mazarbul"}


@app.post("/purchase-orders", response_model=schemas.PurchaseOrder)
def create_po(po: schemas.PurchaseOrderCreate, db: Session = Depends(get_db)):
    db_po = models.PurchaseOrder(**po.dict())
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po
```

### 5.5 CRUD Router Pattern

Routers should follow this pattern per entity:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.PurchaseOrder])
def list_purchase_orders(db: Session = Depends(get_db)):
    return db.query(models.PurchaseOrder).all()


@router.get("/{po_id}", response_model=schemas.PurchaseOrder)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(models.PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    return po


@router.post("/", response_model=schemas.PurchaseOrder)
def create_purchase_order(po: schemas.PurchaseOrderCreate, db: Session = Depends(get_db)):
    db_po = models.PurchaseOrder(**po.dict())
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po


@router.delete("/{po_id}")
def delete_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.query(models.PurchaseOrder).get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    db.delete(po)
    db.commit()
    return {"status": "deleted"}
```

Routers needed: business-cases, wbs, assets, purchase-orders, goods-receipts, resources, allocations, alerts, auth, user-groups, record-access, audit-logs.

### 5.6 Authentication Dependencies (`backend/app/auth.py`)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        role_hierarchy = {"Viewer": 0, "User": 1, "Manager": 2, "Admin": 3}
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 3)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def check_record_access(record_type: str, record_id: int, required_access: str):
    """
    Check if current user has required access to specific record.
    Access levels: Read < Write < Full
    """
    def access_checker(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
        # Admin has full access to everything
        if current_user.role == "Admin":
            return current_user
            
        # Manager has full access to everything  
        if current_user.role == "Manager":
            return current_user
            
        # Check if user is creator (has full access)
        record = db.query(getattr(models, record_type)).get(record_id)
        if record and hasattr(record, 'created_by') and record.created_by == current_user.id:
            return current_user
            
        # Check explicit record access grants
        access_levels = {"Read": 0, "Write": 1, "Full": 2}
        required_level = access_levels.get(required_access, 2)
        
        # Check direct user access
        user_access = db.query(models.RecordAccess).filter(
            models.RecordAccess.record_type == record_type,
            models.RecordAccess.record_id == record_id,
            models.RecordAccess.user_id == current_user.id,
            models.RecordAccess.expires_at.is_(None) or models.RecordAccess.expires_at > datetime.utcnow().isoformat()
        ).first()
        
        if user_access and access_levels.get(user_access.access_level, 0) >= required_level:
            return current_user
            
        # Check group access
        user_groups = db.query(models.UserGroupMembership).filter(
            models.UserGroupMembership.user_id == current_user.id
        ).all()
        
        for membership in user_groups:
            group_access = db.query(models.RecordAccess).filter(
                models.RecordAccess.record_type == record_type,
                models.RecordAccess.record_id == record_id,
                models.RecordAccess.group_id == membership.group_id,
                models.RecordAccess.expires_at.is_(None) or models.RecordAccess.expires_at > datetime.utcnow().isoformat()
            ).first()
            
            if group_access and access_levels.get(group_access.access_level, 0) >= required_level:
                return current_user
                
        # Check department access for User role
        if current_user.role == "User" and record and hasattr(record, 'dept'):
            if record.dept == current_user.department and required_access in ["Read", "Write"]:
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient {required_access} access to {record_type} {record_id}"
        )
        
    return access_checker

def audit_log_change(action: str, table_name: str, record_id: int, old_values: dict = None, new_values: dict = None):
    """Middleware to log all changes to audit trail"""
    def audit_decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if current_user and db:
                audit_entry = models.AuditLog(
                    table_name=table_name,
                    record_id=record_id,
                    action=action,
                    old_values=json.dumps(old_values) if old_values else None,
                    new_values=json.dumps(new_values) if new_values else None,
                    user_id=current_user.id,
                    timestamp=datetime.utcnow().isoformat(),
                    ip_address=kwargs.get('request').client.host if kwargs.get('request') else None
                )
                db.add(audit_entry)
                db.commit()
                
            return await func(*args, **kwargs)
        return wrapper
    return audit_decorator
```

---

## 6. Frontend – Nuxt 4

### 6.1 Nuxt Config (`frontend/nuxt.config.ts`)

```ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      title: 'Mazarbul',
      meta: [
        { name: 'description', content: 'Mazarbul - Chamber of Spend Records' }
      ]
    }
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE || 'http://localhost:8000'
    }
  }
})
```

### 6.2 Global Styles (`frontend/assets/css/main.css`)

```css
:root {
  --color-primary: #1ED760;
  --color-bg: #F7F7F7;
  --color-text: #333333;
  --color-muted: #666666;
  --color-card: #FFFFFF;
  --shadow-soft: 0 10px 25px rgba(0,0,0,0.06);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background-color: var(--color-bg);
  color: var(--color-text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

a {
  color: var(--color-primary);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.header {
  background-color: #ffffff;
  box-shadow: var(--shadow-soft);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 1.5rem;
  font-weight: 700;
}

.header-sub {
  font-size: 0.85rem;
  color: var(--color-muted);
}

.btn-primary {
  background-color: var(--color-primary);
  color: #ffffff;
  border: none;
  padding: 0.6rem 1.3rem;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:hover {
  filter: brightness(0.95);
}

.main-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem 3rem;
}

.card {
  background-color: var(--color-card);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
  padding: 1.5rem;
}

.card-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.card-sub {
  font-size: 0.85rem;
  color: var(--color-muted);
  margin-bottom: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1.2fr);
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
```

### 6.3 Layout (`frontend/layouts/default.vue`)

```vue
<template>
  <div>
    <header class="header">
      <div>
        <div class="header-title">Mazarbul</div>
        <div class="header-sub">Chamber of Spend Records</div>
      </div>
      <nav>
        <NuxtLink to="/" class="mr-4">Dashboard</NuxtLink>
        <NuxtLink to="/purchase-orders">Purchase Orders</NuxtLink>
      </nav>
    </header>
    <main class="main-container">
      <slot />
    </main>
  </div>
</template>
```

### 6.4 Root App (`frontend/app.vue`)

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

### 6.5 Dashboard Page (`frontend/pages/index.vue`)

```vue
<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const health = ref<{ status: string; service: string } | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await $fetch(`${apiBase}/health`)
    health.value = res as any
  } catch (e) {
    console.error(e)
    error.value = 'Failed to reach backend API.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="grid">
    <div class="card">
      <h1 class="card-title">Welcome to Mazarbul</h1>
      <p class="card-sub">
        Track Business Cases, Purchase Orders, Resources, and Goods Receipts — without fighting Excel.
      </p>
      <p>
        This is your StarHub-inspired command center for procurement and resource tracking.
      </p>
      <button class="btn-primary" style="margin-top: 1rem;">
        Create Purchase Order
      </button>
    </div>

    <div class="card">
      <h2 class="card-title">Backend status</h2>
      <p class="card-sub">FastAPI + SQLite</p>

      <p v-if="loading">Checking backend health…</p>
      <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
      <div v-else-if="health">
        <p><strong>Status:</strong> {{ health.status }}</p>
        <p><strong>Service:</strong> {{ health.service }}</p>
      </div>
      <p v-else>Unknown state.</p>
    </div>
  </section>
</template>
```

### 6.6 Purchase Orders Page (`frontend/pages/purchase-orders.vue`)

```vue
<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

interface PurchaseOrder {
  id: number
  po_number: string
  supplier?: string
  total_amount: number
  currency: string
  status?: string
}

const pos = ref<PurchaseOrder[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const fetchPOs = async () => {
  try {
    const res = await $fetch<PurchaseOrder[]>(`${apiBase}/purchase-orders`)
    pos.value = res
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load purchase orders.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchPOs)
</script>

<template>
  <section class="card">
    <h1 class="card-title">Purchase Orders</h1>
    <p class="card-sub">List of all POs from the backend API.</p>

    <p v-if="loading">Loading…</p>
    <p v-else-if="error" style="color: #cc0000;">{{ error }}</p>
    <table v-else class="po-table" style="width:100%; border-collapse:collapse; font-size:0.9rem;">
      <thead>
        <tr>
          <th style="text-align:left; padding:0.5rem 0;">PO Number</th>
          <th style="text-align:left; padding:0.5rem 0;">Supplier</th>
          <th style="text-align:left; padding:0.5rem 0;">Amount</th>
          <th style="text-align:left; padding:0.5rem 0;">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="po in pos" :key="po.id">
          <td style="padding:0.4rem 0;">{{ po.po_number }}</td>
          <td style="padding:0.4rem 0;">{{ po.supplier || '-' }}</td>
          <td style="padding:0.4rem 0;">
            {{ po.total_amount }} {{ po.currency }}
          </td>
          <td style="padding:0.4rem 0;">{{ po.status || 'Open' }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
```

### 6.7 Login Page (`frontend/pages/login.vue`)

```vue
<script setup lang="ts">
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref<string | null>(null)

const login = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await $fetch<{access_token: string, user: any}>(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: form.value.username,
        password: form.value.password
      })
    })
    
    // Store token and redirect
    const token = useCookie('access_token', { httpOnly: true })
    token.value = response.access_token
    
    await navigateTo('/')
  } catch (e: any) {
    error.value = e.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="card-title">Welcome to Mazarbul</h1>
      <p class="card-sub">Please sign in to continue</p>
      
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input 
            id="username" 
            v-model="form.username" 
            type="text" 
            required 
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input 
            id="password" 
            v-model="form.password" 
            type="password" 
            required 
            class="form-input"
          />
        </div>
        
        <p v-if="error" class="error-message">{{ error }}</p>
        
        <button 
          type="submit" 
          :disabled="loading" 
          class="btn-primary login-btn"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

.login-card {
  background: var(--color-card);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-form {
  margin-top: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.1);
}

.login-btn {
  width: 100%;
  margin-top: 1rem;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin: 0.5rem 0;
}
</style>
```

---

## 7. Meta Instructions to the Code LLM

When using this file, you can instruct the LLM:

> You are a coding assistant.  
> Read the file `requirements-codex.md`.  
> - Generate the full backend (FastAPI + SQLAlchemy) based on the spec.  
> - Implement JWT-based authentication with role-based access control.
> - Implement comprehensive audit tracking for all record changes.
> - Implement user groups and record-level access control.
> - Generate CRUD routers for all entities with proper authentication and access control.
> - Add audit logging middleware to track all database changes.
> - Generate the Nuxt 4 frontend, including pages for login, dashboard, purchase orders, and access management.
> - Implement frontend authentication with route guards and role-based UI.
> - Add user group management and record access sharing features in the UI.
> - Ensure the backend runs with `uvicorn app.main:app --reload`.  
> - Ensure the frontend runs with `npm run dev`.  
> - Use the StarHub-inspired CSS theme from the spec.

End of file.
