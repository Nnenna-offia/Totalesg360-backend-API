from typing import Any, Dict, Optional

from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework import status as drf_status



def success_response(data: Any = None, meta: Optional[Dict] = None, status: int = drf_status.HTTP_200_OK) -> Response:
    """Return a standardized success response.

    Format:
    {
      "success": true,
      "data": ...,
      "meta": {...}
    }
    """
    payload = {
        "success": True,
        "data": data if data is not None else {},
    }
    if meta:
        payload["meta"] = meta

    return Response(payload, status=status)


def problem_response(problem: Dict, status_code: int) -> Response:
    """Return a Response containing an RFC7807 problem document (as dict).

    `problem` should contain at least type, title, status, detail.
    Additional extension members (errors, code) are allowed.
    """
    # Ensure minimal keys
    doc = {
        "type": problem.get("type", "about:blank"),
        "title": problem.get("title", _("Error")),
        "status": problem.get("status", status_code),
        "detail": problem.get("detail", ""),
    }
    # optional fields
    for k, v in problem.items():
        if k in doc:
            continue
        doc[k] = v

    return Response(doc, status=status_code)
