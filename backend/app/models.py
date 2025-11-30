from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    department = Column(String(255))
    role = Column(String(50), default="User")  # Viewer, User, Manager, Admin
    is_active = Column(Boolean, default=True)
    created_at = Column(String(32))
    last_login = Column(String(32), nullable=True)

    # Relationships for audit
    # Note: We are not adding back_populates on the User side for every single entity 
    # to avoid cluttering the User model, unless necessary.


class UserGroup(Base):
    __tablename__ = "user_group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))


class UserGroupMembership(Base):
    __tablename__ = "user_group_membership"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    group_id = Column(Integer, ForeignKey("user_group.id"))
    added_by = Column(Integer, ForeignKey("user.id"))
    added_at = Column(String(32))


class RecordAccess(Base):
    __tablename__ = "record_access"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("user_group.id"), nullable=True)
    access_level = Column(String(20), nullable=False)  # Read, Write, Full
    granted_by = Column(Integer, ForeignKey("user.id"))
    granted_at = Column(String(32))
    expires_at = Column(String(32), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(String(32), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)


class BusinessCase(Base):
    __tablename__ = "business_case"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    requestor = Column(String(255))
    dept = Column(String(255))
    estimated_cost = Column(Float)
    status = Column(String(50))
    
    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

    wbs_items = relationship("WBS", back_populates="business_case")


class WBS(Base):
    __tablename__ = "wbs"

    id = Column(Integer, primary_key=True, index=True)
    business_case_id = Column(Integer, ForeignKey("business_case.id"))
    wbs_code = Column(String(255), unique=True)
    description = Column(Text)
    status = Column(String(50))

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

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

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

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
    total_amount = Column(Float)
    currency = Column(String(10))
    status = Column(String(50))

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

    asset = relationship("Asset", back_populates="purchase_orders")
    goods_receipts = relationship("GoodsReceipt", back_populates="po")
    allocations = relationship("ResourcePOAllocation", back_populates="po")


class GoodsReceipt(Base):
    __tablename__ = "goods_receipt"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_order.id"))
    gr_number = Column(String(255), unique=True, index=True)
    gr_date = Column(String(32))
    amount = Column(Float)
    description = Column(Text)

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

    po = relationship("PurchaseOrder", back_populates="goods_receipts")


class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    vendor = Column(String(255))
    role = Column(String(255))
    start_date = Column(String(32))
    end_date = Column(String(32))
    cost_per_month = Column(Float)
    status = Column(String(50))

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

    allocations = relationship("ResourcePOAllocation", back_populates="resource")


class ResourcePOAllocation(Base):
    __tablename__ = "resource_po_allocation"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resource.id"))
    po_id = Column(Integer, ForeignKey("purchase_order.id"))
    allocation_start = Column(String(32))
    allocation_end = Column(String(32))
    expected_monthly_burn = Column(Float)

    # Audit
    created_by = Column(Integer, ForeignKey("user.id"))
    updated_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(String(32))
    updated_at = Column(String(32))

    resource = relationship("Resource", back_populates="allocations")
    po = relationship("PurchaseOrder", back_populates="allocations")