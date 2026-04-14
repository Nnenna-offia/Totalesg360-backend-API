"""API views for reports."""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from common.api import success_response, problem_response
from organizations.models import Organization, RegulatoryFramework
from submissions.models import ReportingPeriod
from reports.models import Report
from reports.services import (
    generate_report,
    export_to_json,
    export_to_csv,
    export_to_html,
    export_to_pdf,
)
from reports.api.serializers import (
    ReportSerializer,
    GenerateReportRequestSerializer,
    GenerateReportResponseSerializer,
    ReportListSerializer,
)


class ReportListView(APIView):
    """GET /api/v1/reports/ - List all reports for organization."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            # Get reports for user's organization
            reports = Report.objects.filter(
                organization=org
            ).order_by('-generated_at')[:50]  # Latest 50
            
            serializer = ReportListSerializer(reports, many=True)
            return success_response(data=serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateReportView(APIView):
    """POST /api/v1/reports/generate/ - Generate a new report."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            # Validate input
            serializer = GenerateReportRequestSerializer(data=request.data)
            if not serializer.is_valid():
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/validation-error",
                    'title': 'Validation error',
                    'detail': str(serializer.errors),
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            report_type = serializer.validated_data.get('report_type')
            framework_id = serializer.validated_data.get('framework_id')
            reporting_period_id = serializer.validated_data.get('reporting_period_id')
            partner_type = serializer.validated_data.get('partner_type', 'none')
            file_format = serializer.validated_data.get('file_format', 'json')
            
            # Get framework if framework_id provided
            framework = None
            if framework_id:
                try:
                    framework = RegulatoryFramework.objects.get(id=framework_id)
                except RegulatoryFramework.DoesNotExist:
                    problem = {
                        'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                        'title': 'Framework not found',
                        'detail': f'Framework {framework_id} not found',
                    }
                    return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            # Get reporting period if provided
            reporting_period = None
            if reporting_period_id:
                try:
                    reporting_period = ReportingPeriod.objects.get(id=reporting_period_id)
                except ReportingPeriod.DoesNotExist:
                    problem = {
                        'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                        'title': 'Reporting period not found',
                        'detail': f'Reporting period {reporting_period_id} not found',
                    }
                    return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            # Generate report
            report = generate_report(
                organization=org,
                report_type=report_type,
                reporting_period=reporting_period,
                framework=framework,
                partner_type=partner_type,
                generated_by=request.user,
                file_format=file_format,
            )
            
            response_data = {
                "report_id": str(report.id),
                "status": report.status,
                "report_type": report.report_type,
                "download_url": f"/api/v1/reports/{report.id}/download/",
                "message": "Report generated successfully",
            }
            
            return success_response(data=response_data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Report generation failed',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportDetailView(APIView):
    """GET /api/v1/reports/{id}/ - Get report details."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, report_id):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            try:
                report = Report.objects.get(
                    id=report_id,
                    organization=org,
                )
            except Report.DoesNotExist:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                    'title': 'Report not found',
                    'detail': f'Report {report_id} not found',
                }
                return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            serializer = ReportSerializer(report)
            return success_response(data=serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportDownloadView(APIView):
    """GET /api/v1/reports/{id}/download/ - Download report in selected format."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, report_id):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            try:
                report = Report.objects.get(
                    id=report_id,
                    organization=org,
                )
            except Report.DoesNotExist:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/not-found",
                    'title': 'Report not found',
                    'detail': f'Report {report_id} not found',
                }
                return problem_response(problem, status.HTTP_404_NOT_FOUND)
            
            # Export based on format
            file_format = request.query_params.get('format', report.file_format)
            
            # TODO: Export functionality would be implemented here
            # For now, return success with link to report summary
            return success_response(
                data={
                    "report_id": str(report.id),
                    "format": file_format,
                    "download_url": report.file_url,
                    "note": "Export functionality to be implemented",
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ESGSummaryReportView(APIView):
    """GET /api/v1/reports/esg-summary/ - Get ESG summary report."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            # Generate or get cached ESG summary report
            report = Report.objects.filter(
                organization=org,
                report_type=Report.ReportType.ESG_SUMMARY,
                status=Report.Status.COMPLETED,
            ).order_by('-generated_at').first()
            
            if not report:
                # Generate a new one
                report = generate_report(
                    organization=org,
                    report_type=Report.ReportType.ESG_SUMMARY,
                    generated_by=request.user,
                )
            
            serializer = ReportSerializer(report)
            return success_response(data=serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GapReportView(APIView):
    """GET /api/v1/reports/gaps/ - Get compliance gap report."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            # Generate or get cached gap report
            report = Report.objects.filter(
                organization=org,
                report_type=Report.ReportType.GAP,
                status=Report.Status.COMPLETED,
            ).order_by('-generated_at').first()
            
            if not report:
                # Generate a new one
                report = generate_report(
                    organization=org,
                    report_type=Report.ReportType.GAP,
                    generated_by=request.user,
                )
            
            serializer = ReportSerializer(report)
            return success_response(data=serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupReportView(APIView):
    """GET /api/v1/reports/group/ - Get group ESG report."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            org = getattr(request, 'organization', None)
            if not org:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/organization-not-found",
                    'title': 'Organization not found',
                    'detail': 'User is not associated with an organization',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            if org.organization_type != Organization.OrganizationType.GROUP:
                problem = {
                    'type': f"{settings.PROBLEM_BASE_URL}/invalid-organization-type",
                    'title': 'Invalid organization type',
                    'detail': 'Organization must be a group to generate group reports',
                }
                return problem_response(problem, status.HTTP_400_BAD_REQUEST)
            
            # Generate or get cached group report
            report = Report.objects.filter(
                organization=org,
                report_type=Report.ReportType.GROUP,
                status=Report.Status.COMPLETED,
            ).order_by('-generated_at').first()
            
            if not report:
                # Generate a new one
                report = generate_report(
                    organization=org,
                    report_type=Report.ReportType.GROUP,
                    generated_by=request.user,
                )
            
            serializer = ReportSerializer(report)
            return success_response(data=serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            problem = {
                'type': f"{settings.PROBLEM_BASE_URL}/server-error",
                'title': 'Server error',
                'detail': str(e),
            }
            return problem_response(problem, status.HTTP_500_INTERNAL_SERVER_ERROR)
