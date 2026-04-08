from django.test import TestCase
from rest_framework.exceptions import ValidationError

from roles.models import Role, Capability, RoleCapability
from roles.api.serializers import RoleSerializer


class RoleCapabilitySyncTests(TestCase):
    def setUp(self):
        self.cap_a, _ = Capability.objects.get_or_create(code='cap_a', defaults={'name': 'Capability A'})
        self.cap_b, _ = Capability.objects.get_or_create(code='cap_b', defaults={'name': 'Capability B'})

    def test_create_role_with_capabilities(self):
        data = {
            'code': 'role_x',
            'name': 'Role X',
            'capabilities': [self.cap_a.id, self.cap_b.id]
        }
        serializer = RoleSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        role = serializer.save()
        self.assertEqual(RoleCapability.objects.filter(role=role).count(), 2)
        codes = set(rc.capability.code for rc in role.role_capabilities.all())
        self.assertEqual(codes, {'cap_a', 'cap_b'})

    def test_update_role_syncs_mappings(self):
        role = Role.objects.create(code='role_y', name='Role Y')
        RoleCapability.objects.create(role=role, capability=self.cap_a)
        # now update to only have cap_b
        serializer = RoleSerializer(instance=role, data={'capabilities': [self.cap_b.id]}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        caps = set(rc.capability.code for rc in updated.role_capabilities.all())
        self.assertEqual(caps, {'cap_b'})

    def test_cannot_modify_system_role_capabilities(self):
        role = Role.objects.create(code='sys_role', name='System Role', is_system=True)
        serializer = RoleSerializer(instance=role, data={'capabilities': [self.cap_a.id]}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError):
            serializer.save()
