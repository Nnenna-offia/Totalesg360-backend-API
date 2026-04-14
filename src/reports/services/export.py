"""Report Export Service - exports reports to PDF, CSV, JSON, HTML."""
import json
import csv
import io
from typing import Dict, Any, Union, BinaryIO


def export_to_json(report_data: Dict[str, Any]) -> str:
    """
    Export report to JSON format.
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        JSON string
    """
    return json.dumps(report_data, indent=2, default=str)


def export_to_csv(report_data: Dict[str, Any]) -> str:
    """
    Export report to CSV format.
    
    Flattens nested structures for CSV compatibility.
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        CSV string
    """
    output = io.StringIO()
    
    # Handle different report structures
    if "esg_score" in report_data:
        # ESG Summary or Framework report
        _export_esg_to_csv(output, report_data)
    elif "total_gaps" in report_data:
        # Gap report
        _export_gaps_to_csv(output, report_data)
    elif "subsidiaries" in report_data:
        # Group report
        _export_group_to_csv(output, report_data)
    
    return output.getvalue()


def export_to_html(report_data: Dict[str, Any], title: str = "Report") -> str:
    """
    Export report to HTML format.
    
    Args:
        report_data: Report data dictionary
        title: HTML page title
    
    Returns:
        HTML string
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 20px;
            }}
            .section {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f9f9f9;
                border-left: 4px solid #3498db;
            }}
            .metric {{
                display: inline-block;
                margin: 10px 20px 10px 0;
            }}
            .metric-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #3498db;
            }}
            .metric-label {{
                font-size: 0.9em;
                color: #7f8c8d;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            table th {{
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            table td {{
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            table tr:hover {{
                background-color: #ecf0f1;
            }}
            .status-open {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .status-in-progress {{
                color: #f39c12;
                font-weight: bold;
            }}
            .status-resolved {{
                color: #27ae60;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 15px;
                border-top: 1px solid #ecf0f1;
                font-size: 0.9em;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{report_data.get('organization', 'Report')}</h1>
            
            {_render_html_sections(report_data)}
            
            <div class="footer">
                <p>Generated: {report_data.get('generated_at', 'N/A')}</p>
                <p>Report Type: {report_data.get('report_type', 'N/A')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def export_to_pdf(report_data: Dict[str, Any], title: str = "Report") -> bytes:
    """
    Export report to PDF format.
    
    Note: Requires weasyprint or reportlab. For now returns HTML as fallback.
    
    Args:
        report_data: Report data dictionary
        title: PDF title
    
    Returns:
        PDF binary data
    """
    # Try to import weasyprint for PDF generation
    try:
        from weasyprint import HTML, CSS
        import io
        
        html_content = export_to_html(report_data, title)
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        return pdf_buffer.getvalue()
    
    except ImportError:
        # Fallback: return HTML as UTF-8 bytes with warning
        html_content = export_to_html(report_data, title)
        warning = "<!-- PDF generation requires weasyprint. Install: pip install weasyprint -->\n"
        return (warning + html_content).encode('utf-8')


def _export_esg_to_csv(output: io.StringIO, report_data: Dict[str, Any]) -> None:
    """Export ESG/Framework report to CSV."""
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ESG Report - Summary"])
    writer.writerow([])
    
    # Organization info
    writer.writerow(["Organization", report_data.get("organization", "")])
    writer.writerow(["Report Period", report_data.get("reporting_period", "")])
    writer.writerow([])
    
    # ESG Scores
    if report_data.get("esg_score"):
        writer.writerow(["ESG Scores"])
        writer.writerow(["Environmental", report_data["esg_score"].get("environmental", "")])
        writer.writerow(["Social", report_data["esg_score"].get("social", "")])
        writer.writerow(["Governance", report_data["esg_score"].get("governance", "")])
        writer.writerow(["Overall", report_data["esg_score"].get("overall", "")])
        writer.writerow([])
    
    # Framework Readiness
    if report_data.get("framework_readiness"):
        writer.writerow(["Framework Readiness"])
        writer.writerow(["Framework", "Coverage %", "Risk Level", "Status"])
        for fw in report_data["framework_readiness"]:
            writer.writerow([
                fw.get("framework", ""),
                fw.get("readiness_percent", ""),
                fw.get("risk_level", ""),
                fw.get("compliance_status", ""),
            ])
        writer.writerow([])
    
    # Gaps
    if report_data.get("gaps") or report_data.get("compliance_gaps"):
        gaps = report_data.get("gaps") or report_data.get("compliance_gaps")
        writer.writerow(["Compliance Gaps"])
        writer.writerow(["Requirement", "Type", "Priority", "Status"])
        for gap in gaps[:10]:
            writer.writerow([
                gap.get("requirement", ""),
                gap.get("gap_type", ""),
                gap.get("priority", ""),
                gap.get("status", ""),
            ])


def _export_gaps_to_csv(output: io.StringIO, report_data: Dict[str, Any]) -> None:
    """Export gap report to CSV."""
    writer = csv.writer(output)
    
    writer.writerow(["Compliance Gap Report"])
    writer.writerow([])
    writer.writerow(["Organization", report_data.get("organization", "")])
    writer.writerow([])
    
    writer.writerow(["Gap Summary"])
    writer.writerow(["Total Gaps", report_data.get("total_gaps", "")])
    writer.writerow(["Critical Gaps", report_data.get("gaps_by_priority", {}).get("critical", "")])
    writer.writerow(["High Priority", report_data.get("gaps_by_priority", {}).get("high", "")])
    writer.writerow(["Open Gaps", report_data.get("gaps_by_status", {}).get("open", "")])
    writer.writerow([])
    
    if report_data.get("critical_gaps"):
        writer.writerow(["Critical Gaps"])
        writer.writerow(["Requirement", "Framework", "Priority", "Status", "Days Open"])
        for gap in report_data["critical_gaps"]:
            writer.writerow([
                gap.get("requirement", ""),
                gap.get("framework", ""),
                gap.get("priority", ""),
                gap.get("status", ""),
                gap.get("days_open", ""),
            ])


def _export_group_to_csv(output: io.StringIO, report_data: Dict[str, Any]) -> None:
    """Export group report to CSV."""
    writer = csv.writer(output)
    
    writer.writerow(["Group ESG Report"])
    writer.writerow([])
    writer.writerow(["Organization", report_data.get("organization", "")])
    writer.writerow(["Type", "Group"])
    writer.writerow([])
    
    if report_data.get("esg_score"):
        writer.writerow(["Group ESG Scores"])
        writer.writerow(["Environmental", report_data["esg_score"].get("environmental", "")])
        writer.writerow(["Social", report_data["esg_score"].get("social", "")])
        writer.writerow(["Governance", report_data["esg_score"].get("governance", "")])
        writer.writerow(["Overall", report_data["esg_score"].get("overall", "")])
        writer.writerow([])
    
    if report_data.get("subsidiaries"):
        writer.writerow(["Subsidiary Ranking"])
        writer.writerow(["Rank", "Name", "Environmental", "Social", "Governance", "Overall"])
        for sub in report_data["subsidiaries"]:
            writer.writerow([
                sub.get("rank", ""),
                sub.get("name", ""),
                sub.get("environmental", ""),
                sub.get("social", ""),
                sub.get("governance", ""),
                sub.get("overall", ""),
            ])


def _render_html_sections(report_data: Dict[str, Any]) -> str:
    """Render HTML sections based on report data."""
    html = ""
    
    # ESG Scores
    if report_data.get("esg_score"):
        html += """
        <div class="section">
            <h2>ESG Scores</h2>
            <div class="metric">
                <div class="metric-value">{}</div>
                <div class="metric-label">Environmental</div>
            </div>
            <div class="metric">
                <div class="metric-value">{}</div>
                <div class="metric-label">Social</div>
            </div>
            <div class="metric">
                <div class="metric-value">{}</div>
                <div class="metric-label">Governance</div>
            </div>
            <div class="metric">
                <div class="metric-value">{}</div>
                <div class="metric-label">Overall</div>
            </div>
        </div>
        """.format(
            report_data["esg_score"].get("environmental", "N/A"),
            report_data["esg_score"].get("social", "N/A"),
            report_data["esg_score"].get("governance", "N/A"),
            report_data["esg_score"].get("overall", "N/A"),
        )
    
    # Summary Info
    if report_data.get("summary"):
        html += """
        <div class="section">
            <h2>Summary</h2>
            <table>
                <tbody>
        """
        for key, value in report_data["summary"].items():
            html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
        html += """
                </tbody>
            </table>
        </div>
        """
    
    return html
