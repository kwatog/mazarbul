from pydantic import BaseModel
from typing import Optional, List


# --- User ---
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    department: Optional[str] = None
    role: Optional[str] = "User"
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    department: Optional[str] = None

class UserResponse(BaseModel):
    message: str
    user: User


# --- UserGroup ---
class UserGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class UserGroupCreate(UserGroupBase):
    pass

class UserGroup(UserGroupBase):
    id: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserGroupMembershipBase(BaseModel):
    user_id: int
    group_id: int

class UserGroupMembershipCreate(UserGroupMembershipBase):
    pass

class UserGroupMembership(UserGroupMembershipBase):
    id: int
    added_by: Optional[int] = None
    added_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# --- RecordAccess ---
class RecordAccessBase(BaseModel):
    record_type: str
    record_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    access_level: str
    expires_at: Optional[str] = None

class RecordAccessCreate(RecordAccessBase):
    pass

class RecordAccessUpdate(BaseModel):
    access_level: Optional[str] = None
    expires_at: Optional[str] = None

class RecordAccess(RecordAccessBase):
    id: int
    granted_by: Optional[int] = None
    granted_at: Optional[str] = None
    updated_by: Optional[int] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- AuditLog ---
class AuditLogBase(BaseModel):
    table_name: str
    record_id: int
    action: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    user_id: Optional[int] = None
    timestamp: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    class Config:
        from_attributes = True


# --- Base Audit Mixin for Schemas ---
class AuditMixin(BaseModel):
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- BudgetItem ---
class BudgetItemBase(BaseModel):
    workday_ref: str
    title: str
    description: Optional[str] = None
    budget_amount: float
    currency: str
    fiscal_year: int
    owner_group_id: int

class BudgetItemCreate(BudgetItemBase):
    pass

class BudgetItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget_amount: Optional[float] = None
    currency: Optional[str] = None
    fiscal_year: Optional[int] = None

class BudgetItem(BudgetItemBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- BusinessCase ---
class BusinessCaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    requestor: Optional[str] = None
    dept: Optional[str] = None
    lead_group_id: Optional[int] = None
    estimated_cost: Optional[float] = None
    status: Optional[str] = "Draft"

class BusinessCaseCreate(BusinessCaseBase):
    pass

class BusinessCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requestor: Optional[str] = None
    dept: Optional[str] = None
    lead_group_id: Optional[int] = None
    estimated_cost: Optional[float] = None
    status: Optional[str] = None

class BusinessCase(BusinessCaseBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- BusinessCaseLineItem ---
class BusinessCaseLineItemBase(BaseModel):
    business_case_id: int
    budget_item_id: int
    owner_group_id: int
    title: str
    description: Optional[str] = None
    spend_category: str  # CAPEX or OPEX
    requested_amount: float
    currency: str
    planned_commit_date: Optional[str] = None
    status: Optional[str] = "Draft"

class BusinessCaseLineItemCreate(BusinessCaseLineItemBase):
    pass

class BusinessCaseLineItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    spend_category: Optional[str] = None
    requested_amount: Optional[float] = None
    currency: Optional[str] = None
    planned_commit_date: Optional[str] = None
    status: Optional[str] = None

class BusinessCaseLineItem(BusinessCaseLineItemBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- WBS ---
class WBSBase(BaseModel):
    business_case_line_item_id: int
    wbs_code: str
    description: Optional[str] = None
    owner_group_id: int
    status: Optional[str] = "Active"

class WBSCreate(WBSBase):
    pass

class WBSUpdate(BaseModel):
    wbs_code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class WBS(WBSBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- Asset ---
class AssetBase(BaseModel):
    wbs_id: int
    asset_code: str
    asset_type: Optional[str] = "CAPEX"
    description: Optional[str] = None
    owner_group_id: int
    status: Optional[str] = "Active"

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    asset_code: Optional[str] = None
    asset_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Asset(AssetBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- PurchaseOrder ---
class PurchaseOrderBase(BaseModel):
    asset_id: int
    po_number: str
    ariba_pr_number: Optional[str] = None
    supplier: Optional[str] = None
    po_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_amount: float
    currency: str
    spend_category: str  # CAPEX or OPEX
    planned_commit_date: Optional[str] = None
    actual_commit_date: Optional[str] = None
    owner_group_id: int
    status: Optional[str] = "Open"

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderUpdate(BaseModel):
    ariba_pr_number: Optional[str] = None
    supplier: Optional[str] = None
    po_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    spend_category: Optional[str] = None
    planned_commit_date: Optional[str] = None
    actual_commit_date: Optional[str] = None
    status: Optional[str] = None

class PurchaseOrder(PurchaseOrderBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- GoodsReceipt ---
class GoodsReceiptBase(BaseModel):
    po_id: int
    gr_number: str
    gr_date: Optional[str] = None
    amount: float
    description: Optional[str] = None
    owner_group_id: int

class GoodsReceiptCreate(GoodsReceiptBase):
    pass

class GoodsReceiptUpdate(BaseModel):
    gr_date: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None

class GoodsReceipt(GoodsReceiptBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- Resource ---
class ResourceBase(BaseModel):
    name: str
    vendor: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cost_per_month: Optional[float] = None
    owner_group_id: int
    status: Optional[str] = "Active"

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cost_per_month: Optional[float] = None
    status: Optional[str] = None

class Resource(ResourceBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- ResourcePOAllocation ---
class ResourcePOAllocationBase(BaseModel):
    resource_id: int
    po_id: int
    allocation_start: Optional[str] = None
    allocation_end: Optional[str] = None
    expected_monthly_burn: Optional[float] = None
    owner_group_id: int

class ResourcePOAllocationCreate(ResourcePOAllocationBase):
    pass

class ResourcePOAllocationUpdate(BaseModel):
    allocation_start: Optional[str] = None
    allocation_end: Optional[str] = None
    expected_monthly_burn: Optional[float] = None

class ResourcePOAllocation(ResourcePOAllocationBase, AuditMixin):
    id: int
    class Config:
        from_attributes = True


# --- Pagination ---
class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100

class PaginatedResponse(BaseModel):
    items: List[BaseModel]
    total: int
    skip: int
    limit: int
