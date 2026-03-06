from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from roles.models import Capability, Role
from .serializers import CapabilitySerializer, RoleSerializer
from common.permissions import HasGlobalCapability


class CapabilityViewSet(viewsets.ModelViewSet):
    queryset = Capability.objects.all().order_by('code')
    serializer_class = CapabilitySerializer
    required_capability = 'manage_roles'

    def get_permissions(self):
        # reads/writes require global capability (staff bypass inside HasGlobalCapability)
        return [IsAuthenticated(), HasGlobalCapability()]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('code')
    serializer_class = RoleSerializer
    required_capability = 'manage_roles'

    def get_permissions(self):
        return [IsAuthenticated(), HasGlobalCapability()]

