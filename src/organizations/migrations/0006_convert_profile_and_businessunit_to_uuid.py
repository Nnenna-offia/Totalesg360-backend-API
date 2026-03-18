from django.db import migrations


SQL = '''
-- Ensure pgcrypto is available for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create new UUID-backed tables
CREATE TABLE IF NOT EXISTS organizations_profile_new (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  registered_business_name varchar(500),
  cac_registration_number varchar(100),
  company_size varchar(20),
  logo varchar(100),
  operational_locations jsonb NOT NULL DEFAULT '[]',
  fiscal_year_start_month smallint,
  fiscal_year_end_month smallint,
  cac_document varchar(100),
  organization_id uuid NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS organizations_businessunit_new (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  name varchar(255) NOT NULL,
  organization_id uuid NOT NULL
);

-- Copy data from old tables, generate new UUIDs
INSERT INTO organizations_profile_new (id, created_at, updated_at, registered_business_name, cac_registration_number, company_size, logo, operational_locations, fiscal_year_start_month, fiscal_year_end_month, cac_document, organization_id)
SELECT gen_random_uuid(), created_at, updated_at, registered_business_name, cac_registration_number, company_size, logo, operational_locations, fiscal_year_start_month, fiscal_year_end_month, cac_document, organization_id
FROM organizations_profile;

INSERT INTO organizations_businessunit_new (id, created_at, updated_at, name, organization_id)
SELECT gen_random_uuid(), created_at, updated_at, name, organization_id
FROM organizations_businessunit;

-- Add foreign key constraints and index on new tables
ALTER TABLE organizations_profile_new
  ADD CONSTRAINT organizations_profile_new_organization_id_fk FOREIGN KEY (organization_id) REFERENCES organizations_organization (id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE organizations_businessunit_new
  ADD CONSTRAINT organizations_businessunit_new_organization_id_fk FOREIGN KEY (organization_id) REFERENCES organizations_organization (id) DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS organizations_businessunit_new_organization_id_idx ON organizations_businessunit_new (organization_id);

-- Swap tables: rename old to *_old, new to original, then drop old
ALTER TABLE organizations_profile RENAME TO organizations_profile_old;
ALTER TABLE organizations_profile_new RENAME TO organizations_profile;
ALTER TABLE organizations_businessunit RENAME TO organizations_businessunit_old;
ALTER TABLE organizations_businessunit_new RENAME TO organizations_businessunit;

DROP TABLE IF EXISTS organizations_profile_old CASCADE;
DROP TABLE IF EXISTS organizations_businessunit_old CASCADE;
'''


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0005_refactor_profile_and_businessunit'),
    ]

    # This migration performs DDL and data-copy steps that must be visible
    # to subsequent operations. Disable the transaction wrapper.
    atomic = False

    operations = [
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]
