from django.core.exceptions import ValidationError
from django.test import TestCase

from organizations.api.serializers import CreateSubsidiarySerializer, OrganizationDetailSerializer
from organizations.models import Organization
from organizations.services.create_organization import create_organization
from organizations.services.hierarchy_validation import validate_hierarchy


class EntityHierarchyValidationTests(TestCase):
    def setUp(self):
        self.group = Organization.objects.create(
            name="TGI Group",
            sector="manufacturing",
            country="NG",
            entity_type=Organization.EntityType.GROUP,
        )

    def test_root_organization_defaults_to_group(self):
        organization = Organization.objects.create(
            name="Standalone Org",
            sector="finance",
            country="NG",
        )

        self.assertEqual(organization.entity_type, Organization.EntityType.GROUP)
        self.assertTrue(organization.is_group())

    def test_non_group_without_parent_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_hierarchy(None, Organization.EntityType.SUBSIDIARY)

    def test_department_cannot_have_children(self):
        subsidiary = Organization.objects.create(
            name="Operations Subsidiary",
            sector="manufacturing",
            country="NG",
            parent=self.group,
            entity_type=Organization.EntityType.SUBSIDIARY,
        )
        department = Organization.objects.create(
            name="ESG Department",
            sector="manufacturing",
            country="NG",
            parent=subsidiary,
            entity_type=Organization.EntityType.DEPARTMENT,
        )

        with self.assertRaises(ValidationError):
            create_organization(
                name="Nested Team",
                sector="manufacturing",
                country="NG",
                primary_reporting_focus=Organization.PrimaryReportingFocus.HYBRID,
                entity_type=Organization.EntityType.DEPARTMENT,
                parent=department,
            )

    def test_create_organization_assigns_subsidiary_under_group(self):
        child = create_organization(
            name="WACOT Rice",
            sector="manufacturing",
            country="NG",
            primary_reporting_focus=Organization.PrimaryReportingFocus.HYBRID,
            parent=self.group,
            entity_type=Organization.EntityType.SUBSIDIARY,
        )

        self.assertEqual(child.parent, self.group)
        self.assertEqual(child.entity_type, Organization.EntityType.SUBSIDIARY)
        self.assertEqual(child.organization_type, Organization.EntityType.SUBSIDIARY)


class EntityHierarchySerializerTests(TestCase):
    def setUp(self):
        self.group = Organization.objects.create(
            name="Parent Group",
            sector="manufacturing",
            country="NG",
            entity_type=Organization.EntityType.GROUP,
        )

    def test_create_subsidiary_serializer_accepts_parent_id_and_entity_type(self):
        serializer = CreateSubsidiarySerializer(
            data={
                "name": "Chi Farms",
                "sector": "manufacturing",
                "country": "NG",
                "entity_type": "subsidiary",
                "parent_id": str(self.group.id),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["parent"], self.group)
        self.assertEqual(serializer.validated_data["entity_type"], Organization.EntityType.SUBSIDIARY)

    def test_organization_detail_serializer_exposes_parent_payload(self):
        child = Organization.objects.create(
            name="Fludor Ghana",
            sector="manufacturing",
            country="NG",
            parent=self.group,
            entity_type=Organization.EntityType.SUBSIDIARY,
        )

        serializer = OrganizationDetailSerializer(child)

        self.assertEqual(serializer.data["entity_type"], Organization.EntityType.SUBSIDIARY)
        self.assertEqual(serializer.data["organization_type"], Organization.EntityType.SUBSIDIARY)
        self.assertEqual(serializer.data["parent"]["id"], str(self.group.id))
        self.assertEqual(serializer.data["parent"]["name"], self.group.name)