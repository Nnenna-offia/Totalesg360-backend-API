import logging
from typing import Any, Dict

from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status

from .exceptions import DomainException
from .api import problem_response

logger = logging.getLogger(__name__)


def _format_validation_errors(detail: Any) -> Dict[str, Any]:
    """Normalize DRF ValidationError.detail into a dict of field -> list[str]."""
    if isinstance(detail, dict):
        errors = {}
        for k, v in detail.items():
            if isinstance(v, (list, tuple)):
                errors[k] = [str(x) for x in v]
            else:
                errors[k] = [str(v)]
        return errors
    # fallback: wrap in non-field errors
    if isinstance(detail, (list, tuple)):
        return {"non_field_errors": [str(x) for x in detail]}
    return {"detail": [str(detail)]}


def custom_exception_handler(exc, context):
    """Convert exceptions into RFC7807 problem details responses.

    - DomainException -> use its `to_problem()`
    - DRF ValidationError -> Problem details with `errors` extension
    - PermissionDenied / NotAuthenticated -> Problem details with 403/401
    - Others: fallback to DRF default and wrap as problem details
    """
    request = context.get("request") if context else None

    # Domain exceptions (raised by services)
    if isinstance(exc, DomainException):
        problem = exc.to_problem(request_path=getattr(request, "path", None))
        return problem_response(problem, exc.status_code)

    # DRF exceptions: let DRF build the default response first
    drf_resp = drf_exception_handler(exc, context)

    # Validation errors
    if isinstance(exc, DRFValidationError):
        errors = _format_validation_errors(exc.detail)
        problem = {
            "type": "https://api.totalesg360.com/problems/validation-error",
            "title": "Validation error",
            "status": drf_status.HTTP_400_BAD_REQUEST,
            "detail": "One or more fields failed validation.",
            "errors": errors,
            "instance": getattr(request, "path", None),
        }
        return problem_response(problem, drf_status.HTTP_400_BAD_REQUEST)

    # Permission and auth errors
    if isinstance(exc, PermissionDenied):
        problem = {
            "type": "https://api.totalesg360.com/problems/forbidden",
            "title": "Permission denied",
            "status": drf_status.HTTP_403_FORBIDDEN,
            "detail": str(exc),
            "instance": getattr(request, "path", None),
        }
        return problem_response(problem, drf_status.HTTP_403_FORBIDDEN)

    if isinstance(exc, NotAuthenticated):
        problem = {
            "type": "https://api.totalesg360.com/problems/not-authenticated",
            "title": "Authentication required",
            "status": drf_status.HTTP_401_UNAUTHORIZED,
            "detail": str(exc),
            "instance": getattr(request, "path", None),
        }
        return problem_response(problem, drf_status.HTTP_401_UNAUTHORIZED)

    # If DRF produced a response (e.g., Http404), convert it into a problem document.
    if drf_resp is not None:
        status_code = drf_resp.status_code
        detail = drf_resp.data
        # attempt to extract a message
        message = None
        if isinstance(detail, dict):
            message = detail.get("detail") or detail
        else:
            message = detail

        problem = {
            "type": "about:blank",
            "title": drf_status.REASON_PHRASES.get(status_code, "Error"),
            "status": status_code,
            "detail": message,
            "instance": getattr(request, "path", None),
        }
        # if detail contains field errors, include them
        if isinstance(detail, dict) and any(k for k in detail.keys() if k != "detail"):
            problem["errors"] = {k: detail[k] for k in detail.keys() if k != "detail"}

        return problem_response(problem, status_code)

    # Unhandled exceptions: log and return 500 problem details
    logger.exception("Unhandled exception during request: %s", getattr(request, "path", "-"))
    problem = {
        "type": "https://api.totalesg360.com/problems/internal-server-error",
        "title": "Internal Server Error",
        "status": drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "An unexpected error occurred.",
        "instance": getattr(request, "path", None),
    }
    return problem_response(problem, drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
