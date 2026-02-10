from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .api import success_response
from .exceptions import OrganizationAlreadyExists


class ExampleCreateOrgView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Example: service raises a DomainException when org exists
        # from organizations.services import create_organization
        from rest_framework.views import APIView
        from rest_framework.permissions import IsAuthenticated
        from rest_framework import status
        from rest_framework.exceptions import ValidationError as DRFValidationError

        from .api import success_response
        from .exceptions import OrganizationAlreadyExists


        class ExampleCreateOrgView(APIView):
            permission_classes = (IsAuthenticated,)

            def post(self, request):
                # Example: service raises a DomainException when org exists
                # from organizations.services import create_organization
                # try:
                #     org = create_organization(request.data)
                # except OrganizationAlreadyExists as exc:
                #     raise
                # For demo, simulate success
                data = {"id": "0001", "name": request.data.get("name")}
                return success_response(data=data, status=status.HTTP_201_CREATED)


        class ExampleErrorDemoView(APIView):
            """Demo endpoint to show how validation and domain errors are converted
            into RFC7807 problem details by the project's DRF exception handler.

            Query params:
            - ?type=validation -> raises a DRF ValidationError
            - ?type=domain -> raises a DomainException (OrganizationAlreadyExists)
            - otherwise -> returns a success response
            """

            permission_classes = (IsAuthenticated,)

            def get(self, request):
                err_type = request.query_params.get("type")

                if err_type == "validation":
                    raise DRFValidationError({"email": ["This field is required."]})

                from rest_framework.views import APIView
                from rest_framework.permissions import IsAuthenticated
                from rest_framework import status
                from rest_framework.exceptions import ValidationError as DRFValidationError

                from .api import success_response
                from .exceptions import OrganizationAlreadyExists, InternalServerError


                class ExampleCreateOrgView(APIView):
                    permission_classes = (IsAuthenticated,)

                    def post(self, request):
                        # Example: service raises a DomainException when org exists
                        # from organizations.services import create_organization
                        # try:
                        #     org = create_organization(request.data)
                        # except OrganizationAlreadyExists as exc:
                        #     raise
                        # For demo, simulate success
                        data = {"id": "0001", "name": request.data.get("name")}
                        return success_response(data=data, status=status.HTTP_201_CREATED)


                class ExampleErrorDemoView(APIView):
                    """Demo endpoint to show how validation and domain errors are converted
                    into RFC7807 problem details by the project's DRF exception handler.

                    Query params:
                    - ?type=validation -> raises a DRF ValidationError
                    - ?type=domain -> raises a DomainException (OrganizationAlreadyExists)
                    - ?type=server -> raises a DomainException representing a 500 error
                    - otherwise -> returns a success response
                    """

                    permission_classes = (IsAuthenticated,)

                    def get(self, request):
                        err_type = request.query_params.get("type")

                        if err_type == "validation":
                            raise DRFValidationError({"email": ["This field is required."]})

                        if err_type == "domain":
                            raise OrganizationAlreadyExists(detail="Demo: organization exists")

                        if err_type == "server":
                            raise InternalServerError(detail="Demo: internal server error")

                        return success_response({"message": "no error", "type": err_type})
