import pytest
from datetime import datetime


def test_bc_creator_has_read_access_always(client, regular_user, user_token, db_session):
    """Test that BusinessCase creator always has Read access."""
    from app.models import BusinessCase

    # Create BC as regular_user
    bc = BusinessCase(
        title="Creator BC",
        description="Test BC created by regular user",
        status="Draft",
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(bc)

    # Regular user should see their own BC in list
    response = client.get(
        "/business-cases",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(item["id"] == bc.id for item in data)

    # Regular user should be able to GET their own BC
    response = client.get(
        f"/business-cases/{bc.id}",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200


def test_bc_creator_can_write_draft_only(client, regular_user, user_token, db_session):
    """Test that BusinessCase creator has audit access (Read only), NOT Write access.

    Per requirements: Creator only has audit access (Read always, not Write).
    Write access requires line-item based access or explicit RecordAccess grant.
    """
    from app.models import BusinessCase, BudgetItem, BusinessCaseLineItem, UserGroupMembership

    # Create a group and add regular_user to it for line-item access
    from app.models import UserGroup
    group = UserGroup(name="Test Creator Group", description="For creator write test")
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    membership = UserGroupMembership(user_id=regular_user.id, group_id=group.id)
    db_session.add(membership)

    # Create budget item owned by the group
    budget = BudgetItem(
        workday_ref="WD-CREATOR-001",
        title="Creator Test Budget",
        budget_amount=50000,
        currency="USD",
        fiscal_year=2025,
        owner_group_id=group.id,
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(budget)

    # Create Draft BC as regular_user
    bc_draft = BusinessCase(
        title="Draft BC",
        description="Draft status BC",
        status="Draft",
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc_draft)
    db_session.commit()
    db_session.refresh(bc_draft)
    db_session.refresh(budget)

    # Create line item linking BC to budget (gives Write access)
    line_item = BusinessCaseLineItem(
        business_case_id=bc_draft.id,
        budget_item_id=budget.id,
        title="Creator Line Item",
        spend_category="CAPEX",
        requested_amount=25000,
        currency="USD",
        owner_group_id=group.id,
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(line_item)
    db_session.commit()

    # Creator should be able to update Draft BC via line-item access
    response = client.put(
        f"/business-cases/{bc_draft.id}",
        json={"description": "Updated description"},
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_bc_line_item_based_access(client, admin_user, regular_user, user_token, test_group, db_session):
    """Test that users can access BC through line-item budget ownership."""
    from app.models import BudgetItem, BusinessCase, BusinessCaseLineItem, UserGroupMembership

    # Add regular_user to test_group
    membership = UserGroupMembership(
        user_id=regular_user.id,
        group_id=test_group.id
    )
    db_session.add(membership)

    # Create budget item owned by test_group
    budget = BudgetItem(
        workday_ref="WD-LINEITEM-001",
        title="Test Budget",
        budget_amount=100000,
        currency="USD",
        fiscal_year=2025,
        owner_group_id=test_group.id,
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(budget)

    # Create BC created by admin (NOT regular_user)
    bc = BusinessCase(
        title="Line Item Access BC",
        description="BC accessible via line item",
        status="Draft",
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(budget)
    db_session.refresh(bc)

    # Create line item linking BC to budget
    line_item = BusinessCaseLineItem(
        business_case_id=bc.id,
        budget_item_id=budget.id,
        title="Test Line Item",
        spend_category="CAPEX",
        requested_amount=50000,
        currency="USD",
        owner_group_id=test_group.id,
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(line_item)
    db_session.commit()

    # Regular user should now see this BC (via line-item access)
    response = client.get(
        "/business-cases",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == bc.id for item in data)

    # Regular user should be able to GET the BC
    response = client.get(
        f"/business-cases/{bc.id}",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200


def test_bc_explicit_record_access_override(client, admin_user, regular_user, user_token, db_session):
    """Test that explicit RecordAccess grants override other rules."""
    from app.models import BusinessCase, RecordAccess

    # Create BC owned by admin
    bc = BusinessCase(
        title="Explicit Access BC",
        description="BC with explicit access grant",
        status="Submitted",
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(bc)

    # Without explicit access, regular_user should NOT see it
    response = client.get(
        "/business-cases",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert not any(item["id"] == bc.id for item in data)

    # Grant explicit Read access to regular_user
    access = RecordAccess(
        record_type="BusinessCase",
        record_id=bc.id,
        user_id=regular_user.id,
        access_level="Read"
    )
    db_session.add(access)
    db_session.commit()

    # Now regular_user should see it
    response = client.get(
        "/business-cases",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == bc.id for item in data)

    # And be able to GET it
    response = client.get(
        f"/business-cases/{bc.id}",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200


def test_bc_status_transition_requires_line_items(client, regular_user, user_token, db_session):
    """Test that BC cannot transition from Draft without line items AND user lacks Write access.

    Per requirements: Creator only has audit access (Read), not Write.
    Status transition requires Write access which comes from line-item based access.
    """
    from app.models import BusinessCase

    # Create Draft BC with NO line items
    bc = BusinessCase(
        title="Empty Draft BC",
        description="BC with no line items",
        status="Draft",
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(bc)

    # Try to transition to Submitted - should fail with 403 (no Write access)
    # NOT 400 because the access check happens before the validation
    response = client.put(
        f"/business-cases/{bc.id}",
        json={"status": "Submitted"},
        cookies={"access_token": user_token}
    )
    assert response.status_code == 403


def test_bc_status_transition_allowed_with_line_items(client, admin_user, regular_user, user_token, test_group, db_session):
    """Test that BC CAN transition from Draft when it has line items."""
    from app.models import BudgetItem, BusinessCase, BusinessCaseLineItem, UserGroupMembership

    # Add regular_user to test_group for line item access
    membership = UserGroupMembership(
        user_id=regular_user.id,
        group_id=test_group.id
    )
    db_session.add(membership)

    # Create budget item
    budget = BudgetItem(
        workday_ref="WD-TRANSITION-001",
        title="Transition Test Budget",
        budget_amount=100000,
        currency="USD",
        fiscal_year=2025,
        owner_group_id=test_group.id,
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(budget)

    # Create Draft BC
    bc = BusinessCase(
        title="Draft with Line Items",
        description="BC that can be transitioned",
        status="Draft",
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(budget)
    db_session.refresh(bc)

    # Add line item
    line_item = BusinessCaseLineItem(
        business_case_id=bc.id,
        budget_item_id=budget.id,
        title="Transition Line Item",
        spend_category="OPEX",
        requested_amount=25000,
        currency="USD",
        owner_group_id=test_group.id,
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(line_item)
    db_session.commit()

    # Now transition should succeed
    response = client.put(
        f"/business-cases/{bc.id}",
        json={"status": "Submitted"},
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Submitted"


def test_bc_no_access_without_line_items_or_creation(client, admin_user, regular_user, user_token, db_session):
    """Test that users cannot access BC if they're not creator and no line-item access exists."""
    from app.models import BusinessCase

    # Create BC as admin with no line items
    bc = BusinessCase(
        title="No Access BC",
        description="BC with no access for regular user",
        status="Draft",
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc)
    db_session.commit()
    db_session.refresh(bc)

    # Regular user should NOT see it in list
    response = client.get(
        "/business-cases",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert not any(item["id"] == bc.id for item in data)

    # Regular user should NOT be able to GET it
    response = client.get(
        f"/business-cases/{bc.id}",
        cookies={"access_token": user_token}
    )
    assert response.status_code == 403


def test_admin_sees_all_business_cases(client, admin_user, regular_user, admin_token, db_session):
    """Test that Admin sees all BusinessCases regardless of access rules."""
    from app.models import BusinessCase

    # Create BCs with different creators
    bc1 = BusinessCase(
        title="Admin BC",
        description="Created by admin",
        status="Draft",
        created_by=admin_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    bc2 = BusinessCase(
        title="User BC",
        description="Created by regular user",
        status="Draft",
        created_by=regular_user.id,
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(bc1)
    db_session.add(bc2)
    db_session.commit()

    # Admin should see both
    response = client.get(
        "/business-cases",
        cookies={"access_token": admin_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    bc_ids = [item["id"] for item in data]
    assert bc1.id in bc_ids
    assert bc2.id in bc_ids
