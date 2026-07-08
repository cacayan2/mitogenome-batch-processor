"""test_markdown_report.py

Unit tests for Markdown report rendering.
"""

# Imports
from pathlib import Path

from mitopipeline.reporting.markdown_report import (
    markdown_table,
    render_sample_report,
    write_sample_report,
)
from mitopipeline.reporting.report_data import (
    collect_sample_report_data,
)
from tests.unit.test_report_data import (
    create_report_outputs,
)


def test_markdown_table():
    """Confirm Markdown tables render correctly."""
    result = markdown_table(
        headers=[
            "Metric",
            "Value",
        ],
        rows=[
            [
                "Reads",
                "100",
            ],
        ],
    )

    assert "| Metric | Value |" in result
    assert "| Reads | 100 |" in result


def test_render_sample_report(
        tmp_path: Path,
):
    """Confirm the report contains all major sections."""
    job_directory = (
        tmp_path
        / "job"
    )

    create_report_outputs(
        job_directory
    )

    report_data = collect_sample_report_data(
        sample_id="sample_001",
        job_directory=job_directory,
    )

    report_path = (
        job_directory
        / "reporting"
        / "sample_001.report.md"
    )

    report = render_sample_report(
        report_data=report_data,
        report_path=report_path,
    )

    assert (
        "# Mitochondrial Genome Report: "
        "sample_001"
        in report
    )

    assert "**Species:** Species one" in report
    assert "## Read trimming and filtering" in report
    assert "## Assembly" in report
    assert "## Annotation" in report
    assert "## Closest BLAST matches" in report
    assert "## Phylogenetic validation" in report
    assert "GTR+F+I+G4" in report
    assert "99.50%" in report


def test_write_sample_report(
        tmp_path: Path,
):
    """Confirm the report is written atomically."""
    job_directory = (
        tmp_path
        / "job"
    )

    create_report_outputs(
        job_directory
    )

    report_data = collect_sample_report_data(
        sample_id="sample_001",
        job_directory=job_directory,
    )

    report_path = (
        job_directory
        / "reporting"
        / "sample_001.report.md"
    )

    result = write_sample_report(
        report_data=report_data,
        output_path=report_path,
    )

    assert result == report_path.resolve()
    assert report_path.exists()
    assert report_path.stat().st_size > 0