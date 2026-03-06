from rest_framework import serializers
from roles.models import Capability, Role
from django.db import transaction
from rest_framework.exceptions import ValidationError


class CapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capability
        fields = ["id", "code", "name", "description"]
        read_only_fields = ["id"]


class RoleSerializer(serializers.ModelSerializer):
    capabilities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Capability.objects.all(), write_only=True, required=False
    )
    assigned_capabilities = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = ["id", "code", "name", "description", "is_system", "capabilities", "assigned_capabilities"]
        read_only_fields = ["id", "is_system", "assigned_capabilities"]

    def create(self, validated_data):
        caps = validated_data.pop('capabilities', [])
        with transaction.atomic():
            role = super().create(validated_data)
            from roles.models import RoleCapability
            to_create = []
            for c in caps:
                to_create.append(RoleCapability(role=role, capability=c))
            if to_create:
                RoleCapability.objects.bulk_create(to_create, ignore_conflicts=True)
        return role

    def update(self, instance, validated_data):
        caps = validated_data.pop('capabilities', None)
        # prevent modification of system roles' capability assignments
        if instance.is_system and caps is not None:
            raise ValidationError({'capabilities': 'Cannot modify capabilities for system roles.'})

        with transaction.atomic():
            role = super().update(instance, validated_data)
            if caps is not None:
                from roles.models import RoleCapability
                existing = {rc.capability_id: rc for rc in role.role_capabilities.all()}
                new_ids = {c.id for c in caps}
                # remove mappings not in new set
                for cap_id, rc in list(existing.items()):
                    if cap_id not in new_ids:
                        rc.delete()
                # add new mappings
                to_create = []
                for c in caps:
                    if c.id not in existing:
                        to_create.append(RoleCapability(role=role, capability=c))
                if to_create:
                    RoleCapability.objects.bulk_create(to_create, ignore_conflicts=True)
        return role

    def get_assigned_capabilities(self, obj):
        # role.role_capabilities are RoleCapability instances; return their related Capability objects
        caps = [rc.capability for rc in obj.role_capabilities.select_related('capability').all()]
        return CapabilitySerializer(caps, many=True).data
