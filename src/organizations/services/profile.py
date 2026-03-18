from typing import Optional
from django.db import transaction
from organizations.models import OrganizationProfile, BusinessUnit, Organization


@transaction.atomic
def update_organization_profile(organization: Organization, **kwargs) -> OrganizationProfile:
    profile, _ = OrganizationProfile.objects.get_or_create(organization=organization)

    # Allowed fields
    allowed = {
        'registered_business_name',
        'cac_registration_number',
        'company_size',
        'logo',
        'operational_locations',
        'fiscal_year_start_month',
        'fiscal_year_end_month',
        'cac_document',
    }

    for k, v in kwargs.items():
        if k in allowed:
            setattr(profile, k, v)

    profile.save()
    return profile


@transaction.atomic
def create_business_unit(organization: Organization, name: str) -> BusinessUnit:
    return BusinessUnit.objects.create(organization=organization, name=name)


@transaction.atomic
def update_business_unit(bu: BusinessUnit, name: str) -> BusinessUnit:
    bu.name = name
    bu.save()
    return bu


@transaction.atomic
def delete_business_unit(bu: BusinessUnit) -> None:
    bu.delete()
