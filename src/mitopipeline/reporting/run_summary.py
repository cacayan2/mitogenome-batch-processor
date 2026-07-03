"""run_summary.py

Build and write run-level summary tables. 
"""

# Imports
from pathlib import Path
import csv

from mitopipeline.models.sample_summary import SampleSummary

def sample_summaries_to_rows(
        sample_summaries: list[SampleSummary],
) -> list[dict]:
    """Convert a list of SampleSummary objects to a list of dictionaries for CSV writing.

    Args:
        sample_summaries: A list of SampleSummary objects.

    Returns:
        A list of dictionaries, where each dictionary represents a row in the CSV file.
    """
    return [summary.to_dict() for summary in sample_summaries]

def write_run_summary(
        sample_summaries: list[SampleSummary],
        output_path: Path,
        delimiter: str = "\t",
) -> None:
    """Write run-level summary table.

    Args:
        sample_summaries: A list of SampleSummary objects.
        output_path: The path to the output CSV file.
        delimiter: The delimiter to use in the CSV file. Defaults to tab.
    
    Returns:
        None
    """

    # Creating output path.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Obtaining rows.
    rows = sample_summaries_to_rows(sample_summaries)

    # Writing empty file if no rows. 
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    
    # Finding names of fields.
    fieldnames = list(rows[0].keys())

    # Writing CSV.
    with output_path.open("w", encoding = "utf-8", newline = "") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames = fieldnames,
            delimiter = delimiter,
            extrasaction = "ignore",
        )

        writer.writeheader()
        writer.writerows(rows)

def write_run_summary_tsv(
        sample_summaries: list[SampleSummary],
        output_path: Path,
) -> None:
    """Write run-level summary table as TSV.

    Args:
        sample_summaries: A list of SampleSummary objects.
        output_path: The path to the output TSV file.
    
    Returns:
        None
    """
    # Writing TSV.
    write_run_summary(
        sample_summaries = sample_summaries,
        output_path = output_path,
        delimiter = "\t",
    )

def write_run_summary_csv(
        sample_summaries: list[SampleSummary],
        output_path: Path,
) -> None:
    """Write run-level summary table as CSV.

    Args:
        sample_summaries: A list of SampleSummary objects.
        output_path: The path to the output CSV file.
    
    Returns:
        None
    """
    # Writing CSV.
    write_run_summary(
        sample_summaries = sample_summaries,
        output_path = output_path,
        delimiter = ",",
    )