"""
JSON report generation
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List
from models.changelog import SchedulerRunSummary

logger = logging.getLogger(__name__)

UTC_PLUS_1 = timezone(timedelta(hours=1))


def generate_json_report(
    summary: SchedulerRunSummary,
    changelogs: List[dict],
    output_dir: str = "reports/output"
) -> str:
    """
    Generate JSON report for a scheduler run
    
    Args:
        summary: Scheduler run summary
        changelogs: List of changelog entries
        output_dir: Directory to save report
        
    Returns:
        Path to generated report file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Build report structure
    report = {
        "summary": {
            "run_id": summary.run_id,
            "started_at": summary.started_at.isoformat(),
            "completed_at": summary.completed_at.isoformat(),
            "duration_seconds": summary.duration_seconds,
            "duration_minutes": round(summary.duration_seconds / 60, 2),
            "total_books_on_site": summary.total_books_on_site,
            "total_books_in_db_before": summary.total_books_in_db_before,
            "total_books_in_db_after": summary.total_books_in_db_after,
            "new_books_added": summary.new_books_added,
            "books_updated": summary.books_updated,
            "books_unchanged": summary.books_unchanged,
            "fields_changed": summary.fields_changed,
            "errors": summary.errors
        },
        "changes": []
    }
    
    # Add all changelogs
    for changelog in changelogs:
        change_entry = {
            "book_source_url": changelog.get("book_source_url"),
            "book_name": changelog.get("book_name"),
            "change_type": changelog.get("change_type"),
            "changes": changelog.get("changes"),
            "changed_at": changelog.get("changed_at").isoformat() if isinstance(changelog.get("changed_at"), datetime) else str(changelog.get("changed_at"))
        }
        report["changes"].append(change_entry)
    
    # Generate filename
    timestamp = summary.started_at.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"change_report_{timestamp}.json"
    filepath = Path(output_dir) / filename
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error generating JSON report: {e}")
        raise


def load_json_report(filepath: str) -> dict:
    """
    Load a JSON report from file
    
    Args:
        filepath: Path to JSON report file
        
    Returns:
        Report data as dictionary
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            report = json.load(f)
        return report
    except Exception as e:
        logger.error(f"Error loading JSON report: {e}")
        raise