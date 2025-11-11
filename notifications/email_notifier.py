"""
Email notification sender
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
from models.changelog import SchedulerRunSummary

load_dotenv()
logger = logging.getLogger(__name__)


class EmailConfig:
    """Email configuration from environment variables"""
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME')


def build_email_body(summary: SchedulerRunSummary) -> str:
    """
    Build HTML email body from summary
    
    Args:
        summary: Scheduler run summary
        
    Returns:
        HTML email body
    """
    # Determine if there are significant changes
    has_changes = summary.new_books_added > 0 or summary.books_updated > 0
    
    status_color = "green" if has_changes else "gray"
    status_text = "Changes Detected" if has_changes else "No Changes"
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .summary-box {{ background-color: #f9f9f9; border-left: 4px solid {status_color}; padding: 15px; margin: 20px 0; }}
            .stats {{ display: table; width: 100%; }}
            .stat-row {{ display: table-row; }}
            .stat-label {{ display: table-cell; padding: 8px; font-weight: bold; width: 60%; }}
            .stat-value {{ display: table-cell; padding: 8px; text-align: right; }}
            .highlight {{ color: #4CAF50; font-weight: bold; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Change Detection Report</h1>
            <p>{summary.started_at.strftime("%B %d, %Y at %H:%M")}</p>
        </div>
        
        <div class="content">
            <div class="summary-box">
                <h2 style="color: {status_color}; margin-top: 0;">{status_text}</h2>
                <p><strong>Run ID:</strong> {summary.run_id}</p>
                <p><strong>Duration:</strong> {summary.duration_seconds / 60:.2f} minutes</p>
            </div>
            
            <h3>Summary Statistics</h3>
            <div class="stats">
                <div class="stat-row">
                    <div class="stat-label">Total Books on Website:</div>
                    <div class="stat-value">{summary.total_books_on_site}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Books in Database (Before):</div>
                    <div class="stat-value">{summary.total_books_in_db_before}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Books in Database (After):</div>
                    <div class="stat-value">{summary.total_books_in_db_after}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">New Books Added:</div>
                    <div class="stat-value"><span class="highlight">{summary.new_books_added}</span></div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Books Updated:</div>
                    <div class="stat-value"><span class="highlight">{summary.books_updated}</span></div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Books Unchanged:</div>
                    <div class="stat-value">{summary.books_unchanged}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Errors:</div>
                    <div class="stat-value">{summary.errors}</div>
                </div>
            </div>
            
            {_build_field_changes_section(summary.fields_changed)}
            
            <p style="margin-top: 30px;">
                Detailed reports (JSON and CSV) are attached to this email.
            </p>
        </div>
        
        <div class="footer">
            <p>This is an automated message from ECommerce Crawler</p>
            <p>Run ID: {summary.run_id}</p>
        </div>
    </body>
    </html>
    """
    
    return html


def _build_field_changes_section(fields_changed: dict) -> str:
    """Build HTML section for field changes"""
    if not fields_changed:
        return ""
    
    html = "<h3>Field Changes Breakdown</h3><div class='stats'>"
    
    for field, count in fields_changed.items():
        html += f"""
        <div class="stat-row">
            <div class="stat-label">{field.replace('_', ' ').title()}:</div>
            <div class="stat-value">{count} changes</div>
        </div>
        """
    
    html += "</div>"
    return html


def send_email_alert(
    summary: SchedulerRunSummary,
    report_files: Optional[List[str]] = None,
    force_send: bool = False
) -> bool:
    """
    Send email alert with change detection summary
    
    Args:
        summary: Scheduler run summary
        report_files: List of report file paths to attach
        force_send: Send email even if no changes detected
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if email is configured
    if not EmailConfig.SMTP_USERNAME or not EmailConfig.ALERT_EMAIL:
        logger.warning("Email not configured, skipping email alert")
        return False
    
    # Only send if there are changes 
    has_changes = summary.new_books_added > 0 or summary.books_updated > 0
    
    if not has_changes and not force_send:
        logger.info("No changes detected, skipping email alert")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{EmailConfig.EMAIL_FROM_NAME} <{EmailConfig.SMTP_USERNAME}>"
        msg['To'] = EmailConfig.ALERT_EMAIL
        msg['Subject'] = f"Change Detection Report - {summary.new_books_added} New, {summary.books_updated} Updated"
        
        # Add body
        html_body = build_email_body(summary)
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach report files
        if report_files:
            for filepath in report_files:
                if Path(filepath).exists():
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(filepath).name}'
                        )
                        msg.attach(part)
        
        # Send email
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls()
            server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email alert sent to {EmailConfig.ALERT_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


def test_email_configuration() -> bool:
    """
    Test email configuration by sending a test email
    
    Returns:
        True if test email sent successfully, False otherwise
    """
    from models.changelog import SchedulerRunSummary
    from datetime import datetime, timezone, timedelta
    
    UTC_PLUS_1 = timezone(timedelta(hours=1))
    
    # Create test summary
    test_summary = SchedulerRunSummary(
        run_id="test_run",
        started_at=datetime.now(UTC_PLUS_1),
        completed_at=datetime.now(UTC_PLUS_1),
        duration_seconds=5.0,
        total_books_on_site=100,
        total_books_in_db_before=95,
        total_books_in_db_after=100,
        new_books_added=5,
        books_updated=2,
        books_unchanged=93,
        fields_changed={"price_incl_tax": 2},
        errors=0
    )
    
    return send_email_alert(test_summary, force_send=True)