"""test_snakemake_workflow.py

Integration tests for the Snakemake workflow.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_snakemake_dry_run():
    """Integration test confirming Snakemake can build the workflow DAG."""

    # Defining fixture output directory.
    output_dir = Path("tests/fixtures/outputs/test_job")

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Running Snakemake dry run.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config.yaml",
                "--dry-run",
                "--cores",
                "1",
            ],
            capture_output=True,
            text=True,
        )

        # Assert statements.
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Building DAG of jobs" in result.stdout
        assert "rule qc_raw" in result.stdout
        assert "rule qc_trimmed" in result.stdout
        assert "rule assembly" in result.stdout
        assert "rule annotation" in result.stdout
        assert "rule phylogeny" in result.stdout
        assert "rule reporting" in result.stdout

    finally:
        # Cleanup.
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_snakemake_placeholder_workflow_execution():
    """Integration test confirming placeholder Snakemake workflow executes."""

    # Defining fixture output directory.
    output_dir = Path("tests/fixtures/outputs/test_job")

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Running Snakemake workflow.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config.yaml",
                "--cores",
                "1",
                "--use-conda",
            ],
            capture_output=True,
            text=True,
        )

        # Defining expected output path.
        report_path = output_dir / "reporting" / "sample_001.report.md"

        # Assert statements.
        assert result.returncode == 0, result.stdout + result.stderr
        assert report_path.exists()
        assert "Report for sample_001" in report_path.read_text()

    finally:
        # Cleanup.
        if output_dir.exists():
            shutil.rmtree(output_dir)