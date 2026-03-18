#!/usr/bin/env python3
import os
import django
import json
import sys

# Ensure project root is on PYTHONPATH so `config` package can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
# If using a different settings module, adjust above.

django.setup()


from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

client = Client()

def pretty(resp):
    try:
        return json.dumps(resp.json(), indent=2)
    except Exception:
        return resp.content.decode('utf-8')

if __name__ == '__main__':
    print('Starting E2E test flow')
    # Check DB connectivity first
    from django.db import connections
    try:
        connections['default'].ensure_connection()
        print('DB connection: OK')
    except Exception as e:
        print('DB connection error:', repr(e))
        print('Aborting E2E run — ensure the database is running and settings are correct.')
        exit(1)

    # 1. Get CSRF
    r = client.get('/api/v1/auth/csrf/')
    print('GET /api/v1/auth/csrf/ ->', r.status_code)
    content = r.content.decode('utf-8', errors='replace')
    print('Response snippet:', content[:1000])
    try:
        body = r.json()
        csrf = body.get('csrf_token')
    except Exception:
        csrf = client.cookies.get('csrftoken').value if client.cookies.get('csrftoken') else None
    print('csrf token length:', len(csrf) if csrf else None)

    # 2. Login
    email = os.environ.get('E2E_EMAIL', 'emmat300005+44@gmail.com')
    password = os.environ.get('E2E_PASSWORD', 'StrongPassw0rd!')
    login_data = {'email': email, 'password': password}
    headers = {'HTTP_X_CSRFTOKEN': csrf} if csrf else {}
    r = client.post('/api/v1/auth/login/', json.dumps(login_data), content_type='application/json', **headers)
    print('POST /api/v1/auth/login/ ->', r.status_code)
    print(pretty(r))

    if r.status_code not in (200, 201):
        print('Login failed; aborting')
        exit(2)

    # 3. Create Indicator
    indicator_payload = {
        'code': 'E2E001',
        'name': 'E2E Test Indicator',
        'description': 'Created by e2e script',
        'pillar': 'ENV',
        'data_type': 'number',
        'unit': 'tCO2e',
        'is_active': True,
        'version': '1.0'
    }
    r = client.post('/api/v1/indicators/', json.dumps(indicator_payload), content_type='application/json', **headers)
    print('POST /api/v1/indicators/ ->', r.status_code)
    print(pretty(r))

    if r.status_code not in (200, 201):
        print('Indicator creation failed; aborting')
        exit(3)

    indicator = r.json()
    indicator_id = indicator.get('id') or indicator.get('uuid') or indicator.get('pk')
    print('Created indicator id:', indicator_id)

    # 4. Create Reporting Period (if endpoint exists)
    rp_payload = {
        'name': 'E2E Period',
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'is_finalized': False
    }
    r = client.post('/api/v1/submissions/reporting-periods/', json.dumps(rp_payload), content_type='application/json', **headers)
    print('POST /api/v1/submissions/reporting-periods/ ->', r.status_code)
    try:
        print(pretty(r))
    except Exception:
        pass

    if r.status_code in (200,201):
        rp = r.json()
        rp_id = rp.get('id') or rp.get('uuid')
    else:
        rp_id = os.environ.get('E2E_REPORTING_PERIOD')

    print('Using reporting_period_id:', rp_id)

    # 5. Submit Activity
    activity_payload = {
        'activity_type_id': os.environ.get('E2E_ACTIVITY_TYPE') or '',
        'reporting_period_id': rp_id,
        'facility_id': os.environ.get('E2E_FACILITY_ID') or '',
        'value': 10.5,
        'unit': 'tCO2e'
    }
    r = client.post('/api/v1/activities/submissions/', json.dumps(activity_payload), content_type='application/json', **headers)
    print('POST /api/v1/activities/submissions/ ->', r.status_code)
    print(pretty(r))

    print('E2E flow complete')
