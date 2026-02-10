from typing import Any, Dict, Optional
from django.utils.translation import gettext_lazy as _


class DomainException(Exception):
    """Base class for domain exceptions raised by services.

    Subclasses should provide `status_code`, `type`, and `title` class attributes.
    Instances may pass a `detail` string and an optional `code` and `errors` dict.
    """
    status_code: int = 500
    type: str = "about:blank"
    title: str = "Domain error"

    def __init__(self, detail: Optional[str] = None, *, code: Optional[str] = None, errors: Optional[Dict[str, Any]] = None):
        super().__init__(detail or self.title)
        self.detail = detail or self.title
        self.code = code
        self.errors = errors or {}

    def to_problem(self, request_path: Optional[str] = None) -> Dict[str, Any]:
        doc = {
            "type": self.type,
            "title": self.title,
            "status": self.status_code,
            "detail": str(self.detail),
        }
        if request_path:
            doc["instance"] = request_path
        if self.errors:
            doc["errors"] = self.errors
        if self.code:
            doc["code"] = self.code
        return doc


# Example exceptions
class OrganizationAlreadyExists(DomainException):
    status_code = 409
    title = "Organization already exists"
    type = "https://api.totalesg360.com/problems/org-already-exists"


class BadRequest(DomainException):
    status_code = 400
    title = "Bad request"
    type = "https://api.totalesg360.com/problems/bad-request"


class InternalServerError(DomainException):
    status_code = 500
    title = "Internal server error"
    type = "https://api.totalesg360.com/problems/internal-server-error"


class Unauthorized(DomainException):
    status_code = 401
    title = "Unauthorized"
    type = "https://api.totalesg360.com/problems/unauthorized"


class Forbidden(DomainException):
    status_code = 403
    title = "Forbidden"
    type = "https://api.totalesg360.com/problems/forbidden"


class NotFound(DomainException):
    status_code = 404
    title = "Not found"
    type = "https://api.totalesg360.com/problems/not-found"


class UnprocessableEntity(DomainException):
    status_code = 422
    title = "Unprocessable entity"
    type = "https://api.totalesg360.com/problems/unprocessable-entity"


class Conflict(DomainException):
    status_code = 409
    title = "Conflict"
    type = "https://api.totalesg360.com/problems/conflict"


class ServiceUnavailable(DomainException):
    status_code = 503
    title = "Service unavailable"
    type = "https://api.totalesg360.com/problems/service-unavailable"
