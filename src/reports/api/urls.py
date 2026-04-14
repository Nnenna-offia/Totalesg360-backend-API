"""URL routing for Reports app."""
from django.urls import path
from reports.api.views import (
    ReportListView,
    GenerateReportView,
    ReportDetailView,
    ReportDownloadView,
    ESGSummaryReportView,
    GapReportView,
    GroupReportView,
)

app_name = 'reports'

urlpatterns = [
    path('', ReportListView.as_view(), name='list'),
    path('generate/', GenerateReportView.as_view(), name='generate'),
    path('<uuid:report_id>/', ReportDetailView.as_view(), name='detail'),
    path('<uuid:report_id>/download/', ReportDownloadView.as_view(), name='download'),
    path('esg-summary/', ESGSummaryReportView.as_view(), name='esg-summary'),
    path('gaps/', GapReportView.as_view(), name='gaps'),
    path('group/', GroupReportView.as_view(), name='group'),
]
