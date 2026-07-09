"""test_run_markdown_report.py

Unit tests for run-level Markdown rendering.
"""

# Imports
from pathlib import Path

from mitopipeline.reporting.run_markdown_report import render_run_report, write_run_report
from mitopipeline.reporting.run_report_data import collect_run_report_data
from tests.unit.test_run_report_data import create_run_report_fixture


def test_render_run_report(tmp_path: Path):
    """Confirm run report contains major sections."""
    create_run_report_fixture(tmp_path)
    run_data = collect_run_report_data(
        job_id="test_job",
        job_directory=tmp_path,
        enabled_stages=["trimming", "assembly", "annotation", "reporting"],
    )
    report = render_run_report(
        run_data=run_data,
        report_path=tmp_path / "reporting" / "run_report.md",
    )
    assert "# MitoPipeline Run Report: test_job" in report
    assert "## Run overview" in report
    assert "## Stage summary" in report
    assert "## Sample status" in report
    assert "## Failed or incomplete samples" in report
    assert "sample_002" in report
    assert "annotation" in report


def test_write_run_report(tmp_path: Path):
    """Confirm run report is written to disk."""
    create_run_report_fixture(tmp_path)
    run_data = collect_run_report_data(
        job_id="test_job",
        job_directory=tmp_path,
        enabled_stages=["trimming", "assembly", "annotation", "reporting"],
    )
    output_path = tmp_path / "reporting" / "run_report.md"
    result = write_run_report(run_data=run_data, output_path=output_path)
    assert result == output_path.resolve()
    assert output_path.exists()
    assert output_path.stat().st_size > 0
