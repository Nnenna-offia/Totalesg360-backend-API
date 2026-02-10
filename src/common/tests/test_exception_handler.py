from types import SimpleNamespace

from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from common.drf import custom_exception_handler
from common.exceptions import OrganizationAlreadyExists


class DRFExceptionHandlerTests(TestCase):
    def test_validation_error_converted_to_problem_details(self):
        exc = DRFValidationError({"email": ["This field is required."]})
        request = SimpleNamespace(path="/api/v1/accounts/signup/")
        context = {"request": request}

        resp = custom_exception_handler(exc, context)

        assert resp.status_code == 400
        data = resp.data
        assert data["type"].endswith("validation-error")
        assert data["title"] == "Validation error"
        assert data["status"] == 400
        assert "errors" in data and data["errors"]["email"] == ["This field is required."]

    def test_domain_exception_converted_to_problem_details(self):
        exc = OrganizationAlreadyExists(detail="Org already exists")
        request = SimpleNamespace(path="/api/v1/organizations/")
        context = {"request": request}

        resp = custom_exception_handler(exc, context)

        assert resp.status_code == 409
        data = resp.data
        assert data["type"].endswith("org-already-exists")
        assert data["title"] == "Organization already exists"
        assert data["status"] == 409
        assert data["detail"] == "Org already exists"
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from common.drf import custom_exception_handler
from common.exceptions import OrganizationAlreadyExists


class DRFExceptionHandlerTests(TestCase):
    def test_validation_error_converted_to_problem_details(self):
        exc = DRFValidationError({"email": ["This field is required."]})
        request = SimpleNamespace(path="/api/v1/accounts/signup/")
        context = {"request": request}

        resp = custom_exception_handler(exc, context)

        assert resp.status_code == 400
        data = resp.data
        assert data["type"].endswith("validation-error")
        assert data["title"] == "Validation error"
        assert data["status"] == 400
        assert "errors" in data and data["errors"]["email"] == ["This field is required."]

    def test_domain_exception_converted_to_problem_details(self):
        exc = OrganizationAlreadyExists(detail="Org already exists")
        request = SimpleNamespace(path="/api/v1/organizations/")
        context = {"request": request}

        resp = custom_exception_handler(exc, context)

        assert resp.status_code == 409
        data = resp.data
        assert data["type"].endswith("org-already-exists")
        assert data["title"] == "Organization already exists"
        assert data["status"] == 409
        assert data["detail"] == "Org already exists"