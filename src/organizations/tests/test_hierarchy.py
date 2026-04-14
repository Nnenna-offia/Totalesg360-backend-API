"""Tests for enterprise organization hierarchy (Layer 1)."""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from organizations.models import Organization
from organizations.selectors.organization_hierarchy import (
    get_organization_tree,
    get_organization_descendants,
    get_organization_ancestors,
    get_organization_statistics,
    is_descendant_of,
    get_root_organization,
)
from organizations.services.organization_hierarchy import (
    create_subsidiary,
    move_subsidiary,
    validate_hierarchy_structure,
)

User = get_user_model()


class OrganizationHierarchyModelTests(TestCase):
    """Test organization hierarchy model methods."""
    
    def setUp(self):
        """Create test organization hierarchy."""
        # Create root organization (Group)
        self.group = Organization.objects.create(
            name="TGI Group",
            sector="manufacturing",
            country="NG",
            organization_type=Organization.OrganizationType.GROUP,
            primary_reporting_focus=Organization.PrimaryReportingFocus.HYBRID,
        )
        
        # Create subsidiary
        self.subsidiary = Organization.objects.create(
            name="WACOT Rice Limited",
            sector="manufacturing",
            country="NG",
            parent=self.group,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
            primary_reporting_focus=Organization.PrimaryReportingFocus.HYBRID,
        )
        
        # Create facility
        self.facility = Organization.objects.create(
            name="Abakaliki Facility",
            sector="manufacturing",
            country="NG",
            parent=self.subsidiary,
            organization_type=Organization.OrganizationType.FACILITY,
            primary_reporting_focus=Organization.PrimaryReportingFocus.HYBRID,
        )
    
    def test_organization_hierarchy_level(self):
        """Test hierarchy_level property."""
        assert self.group.hierarchy_level == 0
        assert self.subsidiary.hierarchy_level == 1
        assert self.facility.hierarchy_level == 2
    
    def test_get_ancestors(self):
        """Test get_ancestors method."""
        # Root org has no ancestors
        ancestors = self.group.get_ancestors()
        assert len(ancestors) == 0
        
        # Subsidiary has group as ancestor
        ancestors = self.subsidiary.get_ancestors()
        assert len(ancestors) == 1
        assert self.group in ancestors
        
        # Facility has subsidiary and group as ancestors
        ancestors = self.facility.get_ancestors()
        assert len(ancestors) == 2
        assert self.subsidiary in ancestors
        assert self.group in ancestors
    
    def test_get_descendants(self):
        """Test get_descendants method."""
        # Get all descendants of group (should include subsidiary and facility)
        descendants = self.group.get_descendants(include_self=False)
        assert len(descendants) == 2
        assert self.subsidiary in descendants
        assert self.facility in descendants
        
        # Get descendants including self
        descendants = self.group.get_descendants(include_self=True)
        assert len(descendants) == 3
        assert self.group in descendants
        assert self.subsidiary in descendants
        assert self.facility in descendants
        
        # Leaf node (facility) has no descendants
        descendants = self.facility.get_descendants(include_self=False)
        assert len(descendants) == 0
    
    def test_str_representation(self):
        """Test string representation includes hierarchy context."""
        assert str(self.group) == "TGI Group"
        assert "subsidiary of" in str(self.subsidiary)
        assert self.group.name in str(self.subsidiary)


class OrganizationHierarchySelectorTests(TestCase):
    """Test hierarchy selector functions."""
    
    def setUp(self):
        """Create test organization hierarchy."""
        self.group = Organization.objects.create(
            name="Energy Group",
            sector="oil_gas",
            country="NG",
            organization_type=Organization.OrganizationType.GROUP,
        )
        
        self.subsidiary1 = Organization.objects.create(
            name="Subsidiary 1",
            sector="oil_gas",
            country="NG",
            parent=self.group,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        self.subsidiary2 = Organization.objects.create(
            name="Subsidiary 2",
            sector="oil_gas",
            country="NG",
            parent=self.group,
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        self.facility = Organization.objects.create(
            name="Production Facility",
            sector="oil_gas",
            country="NG",
            parent=self.subsidiary1,
            organization_type=Organization.OrganizationType.FACILITY,
        )
    
    def test_get_organization_tree(self):
        """Test getting organization tree structure."""
        tree = get_organization_tree(self.group)
        
        assert tree["id"] == str(self.group.id)
        assert tree["name"] == self.group.name
        assert len(tree["subsidiaries"]) == 2
        
        # Check first subsidiary branches off correctly
        sub1_in_tree = [s for s in tree["subsidiaries"] if s["id"] == str(self.subsidiary1.id)][0]
        assert len(sub1_in_tree["subsidiaries"]) == 1
        assert sub1_in_tree["subsidiaries"][0]["id"] == str(self.facility.id)
    
    def test_get_organization_descendants(self):
        """Test getting all descendant organizations."""
        # Get all descendants of group
        descendants = get_organization_descendants(self.group, include_self=False)
        assert descendants.count() == 3
        
        # Filter to only facilities
        facilities = get_organization_descendants(
            self.group,
            include_self=False,
            organization_types=["facility"]
        )
        assert facilities.count() == 1
        assert facilities.first() == self.facility
    
    def test_get_organization_ancestors(self):
        """Test getting all ancestor organizations."""
        ancestors = get_organization_ancestors(self.facility)
        assert len(ancestors) == 2
        assert self.subsidiary1 in ancestors
        assert self.group in ancestors
    
    def test_get_organization_statistics(self):
        """Test getting organization hierarchy statistics."""
        stats = get_organization_statistics(self.group)
        
        assert stats["total_descendants"] == 3
        assert stats["direct_children"] == 2
        assert stats["hierarchy_depth"] == 2
        assert stats["type_breakdown"]["subsidiary"] == 2
        assert stats["type_breakdown"]["facility"] == 1
    
    def test_is_descendant_of(self):
        """Test checking if org is descendant of another."""
        assert is_descendant_of(self.subsidiary1, self.group)
        assert is_descendant_of(self.facility, self.group)
        assert is_descendant_of(self.facility, self.subsidiary1)
        assert not is_descendant_of(self.group, self.subsidiary1)
        assert not is_descendant_of(self.subsidiary1, self.subsidiary2)
    
    def test_get_root_organization(self):
        """Test getting root organization of hierarchy."""
        assert get_root_organization(self.facility) == self.group
        assert get_root_organization(self.subsidiary1) == self.group
        assert get_root_organization(self.group) == self.group


class OrganizationHierarchyServiceTests(TestCase):
    """Test hierarchy service functions."""
    
    def setUp(self):
        """Create test organization."""
        self.parent = Organization.objects.create(
            name="Parent Organization",
            sector="manufacturing",
            country="NG",
            organization_type=Organization.OrganizationType.GROUP,
        )
    
    def test_create_subsidiary(self):
        """Test creating a subsidiary with inherited settings."""
        subsidiary = create_subsidiary(
            parent_organization=self.parent,
            name="New Subsidiary",
            sector="manufacturing",
            country="NG",
            organization_type=Organization.OrganizationType.SUBSIDIARY,
        )
        
        assert subsidiary.parent == self.parent
        assert subsidiary.name == "New Subsidiary"
        assert subsidiary.organization_type == Organization.OrganizationType.SUBSIDIARY
        assert subsidiary.is_active is True
    
    def test_move_subsidiary_circular_reference_check(self):
        """Test that moving subsidiary prevents circular references."""
        subsidiary = create_subsidiary(
            parent_organization=self.parent,
            name="Subsidiary",
            sector="manufacturing",
            country="NG",
        )
        
        # Try to move parent under subsidiary (should fail - circular reference)
        with pytest.raises(ValueError):
            move_subsidiary(self.parent, subsidiary)
    
    def test_validate_hierarchy_structure(self):
        """Test hierarchy validation."""
        subsidiary = create_subsidiary(
            parent_organization=self.parent,
            name="Subsidiary",
            sector="manufacturing",
            country="NG",
        )
        
        # Should pass validation
        is_valid = validate_hierarchy_structure(self.parent)
        assert is_valid is None  # Returns None if valid, raises exception if invalid


class OrganizationHierarchyAPITests(TestCase):
    """Test hierarchy API endpoints."""
    
    def setUp(self):
        """Create test user and organization."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.organization = Organization.objects.create(
            name="Test Organization",
            sector="manufacturing",
            country="NG",
            organization_type=Organization.OrganizationType.GROUP,
        )
        
        # Add user to organization
        from organizations.models import OrganizationMember
        OrganizationMember.objects.create(
            user=self.user,
            organization=self.organization,
        )
    
    def test_hierarchy_endpoint_requires_auth(self):
        """Test that hierarchy endpoint requires authentication."""
        from rest_framework.test import APIClient
        client = APIClient()
        
        response = client.get(
            f"/api/v1/organizations/{self.organization.id}/hierarchy/"
        )
        assert response.status_code == 401
    
    def test_hierarchy_endpoint_requires_membership(self):
        """Test that user must be member of organization."""
        from rest_framework.test import APIClient
        
        other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpass123"
        )
        
        client = APIClient()
        client.force_authenticate(user=other_user)
        
        response = client.get(
            f"/api/v1/organizations/{self.organization.id}/hierarchy/"
        )
        assert response.status_code in [403, 404]
