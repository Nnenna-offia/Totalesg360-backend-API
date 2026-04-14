# Reports App — Layer 8: Reporting & Disclosure Engine

Converts ESG scores, compliance intelligence, framework readiness, and group consolidation into structured reports for stakeholders.

## Architecture

```
reports/
├── models/
│   └── report.py              # Report model (metadata + storage)
├── selectors/
│   ├── esg_summary.py         # ESG summary report aggregation
│   ├── framework_report.py    # Framework compliance reports
│   ├── group_report.py        # Group-level ESG reports (uses Layer 7)
│   ├── gap_report.py          # Compliance gap reports
│   └── partner_report.py      # Partner-specific formats (DEG, USAID, GCF, FRC)
├── services/
│   ├── report_generator.py    # Generate and store reports
│   └── export.py              # JSON, CSV, HTML, PDF export
├── api/
│   ├── views.py               # API endpoints
│   ├── serializers.py         # Request/response serializers
│   └── urls.py                # URL routing
├── signals.py                 # Auto-regeneration on data changes
├── apps.py                    # App configuration
├── admin.py                   # Django admin
└── __init__.py
```

## Key Design Decisions

### 1. **No Duplicate Calculations**
- **Reuses existing layers** via selectors pattern
- Layer 5: Compliance Intelligence (gaps, recommendations)
- Layer 6: ESG Scoring (environmental, social, governance)
- Layer 7: Group Consolidation (subsidiary aggregation)

### 2. **Five Report Types**
- **ESG Summary**: Comprehensive ESG score + framework readiness + gaps
- **Framework Reports**: Per-framework compliance status (GRI, ISSB, SASB, etc.)
- **Group Reports**: Parent-level aggregation with subsidiary rankings
- **Gap Reports**: Compliance gaps grouped by priority + remediation timeline
- **Partner Reports**: Stakeholder-specific formats

### 3. **Multiple Export Formats**
- **JSON**: Default for API responses
- **CSV**: Tabular data for Excel/analytics
- **HTML**: Embeddable reports in web applications
- **PDF**: Printable stakeholder reports

### 4. **Automatic Report Regeneration**
- Signals on ESGScore, FrameworkReadiness, ComplianceGap changes
- Refreshes cached reports automatically
- TTL-based cache expiration (1 hour default)

### 5. **Partner-Specific Formatting**
Supports development finance partners with customized fields:
- **DEG**: Environmental + Social Impact focus
- **USAID**: Development Outcomes + Environmental
- **GCF**: Climate Action emphasis
- **FRC**: Recovery + Climate Resilience

## Database Model

```python
class Report(BaseModel):
    organization          # FK to Organization
    report_type          # ESG_SUMMARY|FRAMEWORK|GROUP|GAP|PARTNER
    framework            # FK (optional) for Framework reports
    partner_type         # DEG|USAID|GCF|FRC|NONE
    reporting_period_id  # UUID of period
    generated_by         # FK to User
    status              # PENDING|GENERATING|COMPLETED|FAILED
    file_url            # Download link (S3/CDN)
    file_format         # json|csv|html|pdf
    metadata            # Report parameters (JSONField)
    summary             # Quick-access summary stats (JSONField)
    generated_at        # Timestamp
    expires_at          # Cache invalidation time
```

## API Endpoints

### List Reports
```
GET /api/v1/reports/
```
Returns all reports for user's organization.

### Generate Report
```
POST /api/v1/reports/generate/
Content-Type: application/json

{
  "report_type": "esg_summary",
  "reporting_period_id": "uuid",
  "framework_id": "uuid",  # for framework reports
  "partner_type": "deg",   # for partner reports
  "file_format": "json"
}
```

Response:
```json
{
  "report_id": "uuid",
  "status": "generating|completed|failed",
  "report_type": "esg_summary",
  "download_url": "/api/v1/reports/uuid/download/",
  "message": "Report generated successfully"
}
```

### Get Report Details
```
GET /api/v1/reports/{id}/
```

### Download Report
```
GET /api/v1/reports/{id}/download/?format=pdf
```

### Get ESG Summary Report
```
GET /api/v1/reports/esg-summary/
```
Auto-generates or returns cached ESG summary (1-hour TTL).

### Get Compliance Gap Report
```
GET /api/v1/reports/gaps/
```

### Get Group ESG Report
```
GET /api/v1/reports/group/
```
Only for group organizations.

## Report Data Structures

### ESG Summary Report
```python
{
    "organization": "TGI Ltd",
    "reporting_period": "2026 Annual",
    "esg_score": {
        "environmental": 42.5,
        "social": 45.0,
        "governance": 40.5,
        "overall": 42.7
    },
    "framework_readiness": [
        {
            "framework": "GRI",
            "readiness_percent": 62.0,
            "risk_level": "medium",
            "mandatory_coverage": 75.0
        }
    ],
    "compliance_gaps": [...],
    "recommendations": [...],
    "summary": {
        "total_frameworks": 5,
        "critical_gaps": 3,
        "overall_esg_rating": "MODERATE"
    }
}
```

### Framework Report
```python
{
    "framework": "GRI",
    "framework_name": "Global Reporting Initiative",
    "organization": "TGI Ltd",
    "readiness": {
        "coverage_percent": 62.0,
        "risk_level": "medium",
        "mandatory_coverage": 75.0
    },
    "gaps": [
        {
            "requirement": "GG4.1 Environmental Policy",
            "gap_type": "missing_data",
            "priority": "high",
            "status": "open"
        }
    ],
    "recommendations": [...],
    "summary": {
        "compliance_status": "SUBSTANTIALLY_COMPLIANT"
    }
}
```

### Group Report
```python
{
    "organization": "TGI Group",
    "organization_type": "Group",
    "esg_score": {
        "environmental": 42.5,
        "social": 45.0,
        "governance": 40.5,
        "overall": 42.7,
        "subsidiary_count": 6
    },
    "subsidiaries": [
        {
            "rank": 1,
            "name": "TGI Ltd",
            "overall": 50.0
        }
    ],
    "summary": {
        "total_subsidiaries": 6,
        "reporting_coverage_percent": 100.0
    }
}
```

### Gap Report
```python
{
    "organization": "TGI Ltd",
    "total_gaps": 15,
    "gaps_by_priority": {
        "critical": 3,
        "high": 5,
        "medium": 4,
        "low": 3
    },
    "critical_gaps": [...],
    "recommendations": [...],
    "summary": {
        "gap_resolution_progress": "MODERATE",
        "critical_count": 8
    }
}
```

### Partner Report (DEG Example)
```python
{
    "report_type": "DEG",
    "partner": "Deutsche Entwicklungsgesellschaft",
    "environmental_impact": {
        "score": 42.5,
        "assessment": "Moderate",
        "key_areas": [...]
    },
    "social_impact": {
        "score": 45.0,
        "assessment": "Good"
    },
    "priority_actions": [...],
    "summary": {
        "overall_readiness": "MODERATE",
        "critical_issues": 3
    }
}
```

## Selectors

### esg_summary.py
```python
get_esg_summary_report(organization, reporting_period=None)
```
- Aggregates ESG scores from Layer 6
- Combines framework readiness from Layer 5
- Includes top gaps and recommendations
- Returns comprehensive ESG overview

### framework_report.py
```python
get_framework_report(organization, framework, reporting_period_id=None)
```
- Framework-specific compliance status
- Gaps and recommendations filtered to framework
- Risk level and readiness metrics

### group_report.py
```python
get_group_esg_report(parent_organization, reporting_period=None)
```
- Uses Layer 7 dashboards and selectors
- Subsidiary rankings by ESG score
- Group-level aggregation

### gap_report.py
```python
get_gap_report(organization)
```
- All gaps grouped by priority
- Resolution progress metrics
- Remediation timeline summaries

### partner_report.py
```python
get_partner_report(organization, partner_type="deg")
```
- Formats to partner expectations
- Supports: DEG, USAID, GCF, FRC
- Custom field emphasis per partner

## Services

### report_generator.py
```python
generate_report(
    organization,
    report_type,
    reporting_period=None,
    framework=None,
    partner_type="none",
    generated_by=None,
    file_format="json"
)
```
- Calls appropriate selector
- Stores in database with metadata
- Sets expiration time
- Registers in admin panel

### export.py
```python
export_to_json(report_data)       # Returns JSON string
export_to_csv(report_data)        # Returns CSV string
export_to_html(report_data)       # Returns HTML page
export_to_pdf(report_data)        # Returns PDF bytes
```

## Caching & TTL

- **Cache Key**: `report:{organization_id}:{report_type}:{framework_id}`
- **Default TTL**: 1 hour (3600s)
- **Auto-refresh**: On any ESGScore, FrameworkReadiness, ComplianceGap change
- **Expiration**: Via `expires_at` field

## Signals

```python
@receiver(post_save, ESGScore)              → regenerate all reports
@receiver(post_save, FrameworkReadiness)    → regenerate all reports
@receiver(post_save, ComplianceGapPriority) → regenerate all reports
@receiver(post_save, ComplianceRecommendation) → regenerate all reports
```

## Testing

Run tests:
```bash
python manage.py test reports.tests
```

Test coverage:
- ESG summary report generation
- Framework report filtering
- Group report aggregation
- Gap report prioritization
- Partner report formatting
- Export to all formats
- Signal-triggered regeneration

## Performance Considerations

1. **Lazy Loading**: Reports generated on-demand (first request)
2. **Caching**: 1-hour TTL prevents regeneration on every request
3. **Batch Processing**: Group reports pre-compute subsidiary rankings
4. **Pagination**: Report lists limited to 50 most recent
5. **Selective Fields**: JSON responses only include required data

## Future Enhancements

1. **Real-time Report Streaming**: WebSocket updates as data changes
2. **Advanced Filters**: Custom date ranges, subsidiary selection
3. **Report Scheduling**: Auto-generate at period close
4. **Email Delivery**: Auto-send reports to stakeholders
5. **Benchmarking**: Compare organization to sector averages
6. **Anomaly Detection**: Flag unusual score changes
7. **Historical Trends**: Multi-period trend analysis
8. **Custom Report Builder**: User-defined report templates

## Integration Points

- **Layer 5** (Compliance): Gap and recommendation data
- **Layer 6** (ESG Scoring): Environmental, social, governance scores
- **Layer 7** (Group Analytics): Subsidiary aggregation and ranking
- **Authentication**: Via accounts middleware
- **Storage**: File URLs (S3/CDN ready)

## Error Handling

All endpoints return RFC7807 problem documents:

```json
{
  "type": "https://totalesg360.com/probs/organization-not-found",
  "title": "Organization not found",
  "detail": "User is not associated with an organization",
  "status": 400
}
```

---

**This completes Layer 8 — Reporting & Disclosure Engine.**
