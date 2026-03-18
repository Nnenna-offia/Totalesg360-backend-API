#!/usr/bin/env python
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django
django.setup()

from roles.models import Capability, Role, RoleCapability
from accounts.models import User

email = 'emmat300005+44@gmail.com'
org_id = '65b4e4ce-3795-4787-82ac-09021d73e0eb'

cap, created = Capability.objects.get_or_create(code='approve_submission', defaults={'name': 'Approve submission'})
print('cap:', cap.code, 'created=', created)

for role_code in ['org_owner', 'org_admin']:
    role = Role.objects.filter(code=role_code).first()
    print('role', role_code, 'exists=', bool(role))
    if role:
        rc, rcreated = RoleCapability.objects.get_or_create(role=role, capability=cap)
        print('rolecap for', role_code, 'created=', rcreated)

user = User.objects.filter(email=email).first()
print('user exists:', bool(user))
if user:
    m = user.memberships.filter(organization__id=org_id, is_active=True).select_related('role').first()
    print('membership exists:', bool(m), 'role:', m.role.code if m else None)
    caps = list(m.role.role_capabilities.values_list('capability__code', flat=True)) if m else []
    print('role caps:', caps)
