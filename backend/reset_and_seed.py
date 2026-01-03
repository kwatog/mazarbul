#!/usr/bin/env python3
"""
Database Reset and Seed Script for Ebrose

This script:
1. Deletes the existing SQLite database
2. Creates all tables from scratch
3. Seeds initial data (admin user, groups, sample records)

Usage:
    python reset_and_seed.py
"""

import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine, SessionLocal
from app import models
from app.auth import get_password_hash, now_utc


def reset_database():
    """Delete existing database file."""
    db_file = "ebrose.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✓ Deleted existing database: {db_file}")
    else:
        print("✓ No existing database found")


def create_tables():
    """Create all tables from models."""
    Base.metadata.create_all(bind=engine)
    print("✓ Created all database tables")


def seed_data():
    """Seed initial data."""
    db = SessionLocal()
    try:
        now = now_utc()

        # 1. Create Admin User
        admin_user = models.User(
            username="admin",
            email="admin@ebrose.local",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            department="IT",
            role="Admin",
            is_active=True,
            created_at=now
        )
        db.add(admin_user)
        db.flush()  # Get ID without committing
        print(f"✓ Created admin user (ID: {admin_user.id})")

        # 2. Create Manager User
        manager_user = models.User(
            username="manager",
            email="manager@ebrose.local",
            hashed_password=get_password_hash("manager123"),
            full_name="Finance Manager",
            department="Finance",
            role="Manager",
            is_active=True,
            created_at=now
        )
        db.add(manager_user)
        db.flush()
        print(f"✓ Created manager user (ID: {manager_user.id})")

        # 3. Create Regular User
        regular_user = models.User(
            username="user",
            email="user@ebrose.local",
            hashed_password=get_password_hash("user123"),
            full_name="Regular User",
            department="Operations",
            role="User",
            is_active=True,
            created_at=now
        )
        db.add(regular_user)
        db.flush()
        print(f"✓ Created regular user (ID: {regular_user.id})")

        # 4. Create User Groups
        finance_group = models.UserGroup(
            name="Finance",
            description="Finance department group",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(finance_group)
        db.flush()
        print(f"✓ Created Finance group (ID: {finance_group.id})")

        ops_group = models.UserGroup(
            name="Operations",
            description="Operations department group",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(ops_group)
        db.flush()
        print(f"✓ Created Operations group (ID: {ops_group.id})")

        it_group = models.UserGroup(
            name="IT",
            description="IT department group",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(it_group)
        db.flush()
        print(f"✓ Created IT group (ID: {it_group.id})")

        # 5. Add users to groups
        db.add(models.UserGroupMembership(
            user_id=manager_user.id,
            group_id=finance_group.id,
            added_by=admin_user.id,
            added_at=now
        ))
        db.add(models.UserGroupMembership(
            user_id=regular_user.id,
            group_id=ops_group.id,
            added_by=admin_user.id,
            added_at=now
        ))
        db.add(models.UserGroupMembership(
            user_id=admin_user.id,
            group_id=it_group.id,
            added_by=admin_user.id,
            added_at=now
        ))
        print("✓ Added users to groups")

        # 6. Create Sample Budget Item
        budget_item = models.BudgetItem(
            workday_ref="WD-2025-FIN-001",
            title="Cloud Infrastructure Budget 2025",
            description="Annual budget for AWS cloud services",
            budget_amount=500000.00,
            currency="USD",
            fiscal_year=2025,
            owner_group_id=finance_group.id,
            created_by=admin_user.id,
            created_at=now
        )
        db.add(budget_item)
        db.flush()
        print(f"✓ Created budget item (ID: {budget_item.id})")

        # 7. Create Sample Business Case
        business_case = models.BusinessCase(
            title="Cloud Migration Project",
            description="Migrate legacy systems to AWS cloud infrastructure",
            requestor="IT Department",
            dept="IT",
            lead_group_id=it_group.id,
            estimated_cost=250000.00,
            status="Approved",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(business_case)
        db.flush()
        print(f"✓ Created business case (ID: {business_case.id})")

        # 8. Create Business Case Line Item
        line_item = models.BusinessCaseLineItem(
            business_case_id=business_case.id,
            budget_item_id=budget_item.id,
            owner_group_id=it_group.id,
            title="AWS EC2 Infrastructure",
            description="Compute resources for migrated applications",
            spend_category="OPEX",
            requested_amount=150000.00,
            currency="USD",
            planned_commit_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
            status="Approved",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(line_item)
        db.flush()
        print(f"✓ Created business case line item (ID: {line_item.id})")

        # 9. Create WBS (inherits owner_group_id from line_item)
        wbs = models.WBS(
            business_case_line_item_id=line_item.id,
            wbs_code="WBS-2025-IT-001",
            description="Cloud Migration Phase 1",
            owner_group_id=line_item.owner_group_id,  # Inherited
            status="Active",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(wbs)
        db.flush()
        print(f"✓ Created WBS (ID: {wbs.id})")

        # 10. Create Asset (inherits owner_group_id from wbs)
        asset = models.Asset(
            wbs_id=wbs.id,
            asset_code="ASSET-AWS-EC2-001",
            asset_type="CAPEX",
            description="AWS EC2 Production Cluster",
            owner_group_id=wbs.owner_group_id,  # Inherited
            status="Active",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(asset)
        db.flush()
        print(f"✓ Created asset (ID: {asset.id})")

        # 11. Create Purchase Order (inherits owner_group_id from asset)
        po = models.PurchaseOrder(
            asset_id=asset.id,
            po_number="PO-2025-001",
            ariba_pr_number="PR-2025-AWS-001",
            supplier="Amazon Web Services",
            po_type="Service",
            start_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 1, 31, tzinfo=timezone.utc),
            total_amount=120000.00,
            currency="USD",
            spend_category="OPEX",
            planned_commit_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            actual_commit_date=datetime(2025, 1, 20, tzinfo=timezone.utc),
            owner_group_id=asset.owner_group_id,  # Inherited
            status="Open",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(po)
        db.flush()
        print(f"✓ Created purchase order (ID: {po.id})")

        # 12. Create Goods Receipt (inherits owner_group_id from po)
        gr = models.GoodsReceipt(
            po_id=po.id,
            gr_number="GR-2025-001",
            gr_date=datetime(2025, 2, 15, tzinfo=timezone.utc),
            amount=10000.00,
            description="First month AWS services",
            owner_group_id=po.owner_group_id,  # Inherited
            created_by=admin_user.id,
            created_at=now
        )
        db.add(gr)
        db.flush()
        print(f"✓ Created goods receipt (ID: {gr.id})")

        # 13. Create Resource
        resource = models.Resource(
            name="John Smith",
            vendor="TechCorp Consulting",
            role="Cloud Architect",
            start_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
            cost_per_month=15000.00,
            owner_group_id=it_group.id,
            status="Active",
            created_by=admin_user.id,
            created_at=now
        )
        db.add(resource)
        db.flush()
        print(f"✓ Created resource (ID: {resource.id})")

        # 14. Create Resource-PO Allocation (inherits owner_group_id from po)
        allocation = models.ResourcePOAllocation(
            resource_id=resource.id,
            po_id=po.id,
            allocation_start=datetime(2025, 2, 1, tzinfo=timezone.utc),
            allocation_end=datetime(2025, 12, 31, tzinfo=timezone.utc),
            expected_monthly_burn=15000.00,
            owner_group_id=po.owner_group_id,  # Inherited
            created_by=admin_user.id,
            created_at=now
        )
        db.add(allocation)
        db.flush()
        print(f"✓ Created resource allocation (ID: {allocation.id})")

        # Commit all changes
        db.commit()
        print("\n✅ Database seeded successfully!")
        print("\n📝 Login Credentials:")
        print("   Admin:   admin / admin123")
        print("   Manager: manager / manager123")
        print("   User:    user / user123")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


def main():
    """Main execution."""
    print("=" * 60)
    print("Ebrose Database Reset & Seed")
    print("=" * 60)
    print()

    reset_database()
    create_tables()
    seed_data()

    print()
    print("=" * 60)
    print("✅ All done! Database is ready to use.")
    print("=" * 60)


if __name__ == "__main__":
    main()
