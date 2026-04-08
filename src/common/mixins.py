from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from organizations.services import validate_user_organization
from common.api import problem_response


class OrganizationAccessMixin:
    """Mixin that validates X-ORG-ID header and membership.

    On success attaches `request.organization` and returns nothing. On
    failure raises DRF exceptions which DRF will render as proper HTTP
    responses.
    """

    def initial(self, request, *args, **kwargs):
        # run usual initialization (auth, etc.) first
        super_initial = getattr(super(), 'initial', None)
        if callable(super_initial):
            super_initial(request, *args, **kwargs)

        # validate and attach organization
        org = validate_user_organization(request)
        request.organization = org
