"""
CSV report generation
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from models.changelog import SchedulerRunSummary

logger = logging.getLogger(__name__)


def generate_csv_report(
    summary: SchedulerRunSummary,
    changelogs: List[dict],
    output_dir: str = "reports/output"
) -> str:
    """
    Generate CSV report for a scheduler run
    
    Args:
        summary: Scheduler run summary
        changelogs: List of changelog entries
        output_dir: Directory to save report
        
    Returns:
        Path to generated report file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = summary.started_at.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"change_report_{timestamp}.csv"
    filepath = Path(output_dir) / filename
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Book Name',
                'Change Type',
                'Field Changed',
                'Old Value',
                'New Value',
                'Changed At',
                'Book URL'
            ])
            
            # Write changes
            for changelog in changelogs:
                book_name = changelog.get("book_name", "Unknown")
                change_type = changelog.get("change_type", "unknown")
                changed_at = changelog.get("changed_at")
                book_url = changelog.get("book_id", "")
                
                # Format changed_at
                if isinstance(changed_at, datetime):
                    changed_at_str = changed_at.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    changed_at_str = str(changed_at)
                
                changes = changelog.get("changes")
                
                if change_type == "added":
                    # New book - single row
                    writer.writerow([
                        book_name,
                        'Added',
                        'N/A',
                        'N/A',
                        'N/A',
                        changed_at_str,
                        book_url
                    ])
                else:
                    # Updated book - one row per field change
                    if changes:
                        for field_name, field_change in changes.items():
                            old_value = field_change.get('old', 'N/A')
                            new_value = field_change.get('new', 'N/A')
                            
                            writer.writerow([
                                book_name,
                                'Updated',
                                field_name,
                                old_value,
                                new_value,
                                changed_at_str,
                                book_url
                            ])
            
            # Write summary at the end
            writer.writerow([])
            writer.writerow(['SUMMARY'])
            writer.writerow(['Run ID', summary.run_id])
            writer.writerow(['Duration (minutes)', round(summary.duration_seconds / 60, 2)])
            writer.writerow(['Total Books on Site', summary.total_books_on_site])
            writer.writerow(['New Books Added', summary.new_books_added])
            writer.writerow(['Books Updated', summary.books_updated])
            writer.writerow(['Books Unchanged', summary.books_unchanged])
            writer.writerow(['Errors', summary.errors])
            
            if summary.fields_changed:
                writer.writerow([])
                writer.writerow(['FIELD CHANGE STATISTICS'])
                for field, count in summary.fields_changed.items():
                    writer.writerow([field, count])
        
        logger.info(f"CSV report generated: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error generating CSV report: {e}")
        raise