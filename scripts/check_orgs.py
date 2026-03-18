#!/usr/bin/env python
"""Quick helper to check organizations in the database."""
import os
import sys
import django
from pathlib import Path

# Add paths like manage.py does
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from organizations.models import Organization

orgs = Organization.objects.values('id', 'name').order_by('id')
if orgs:
    print("Available organizations:")
    for o in orgs:
        print(f"  ID: {o['id']}, Name: {o['name']}")
else:
    print("No organizations found in database.")
    print("\nTo create one, run:")
    print("  ./manage.py shell")
    print("  from organizations.models import Organization")
    print("  Organization.objects.create(name='Test Org', slug='test-org')")
