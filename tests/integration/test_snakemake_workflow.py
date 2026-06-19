"""test_snakemake_workflow.py

Integration tests for the Snakemake workflow.
"""

# Imports
from pathlib import Path
import shutil
import subprocess


def test_snakemake_dry_run():
    """Integration test confirming Snakemake can build the workflow DAG."""

    output_dir = Path("tests/fixtures/outputs/test_job")

    if output_dir.exists():
        shutil.rmtree(output_dir)

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

    assert result.returncode == 0
    assert "Building DAG of jobs" in result.stdout
    assert "rule qc" in result.stdout
    assert "rule trimming" in result.stdout
    assert "rule assembly" in result.stdout
    assert "rule annotation" in result.stdout
    assert "rule phylogeny" in result.stdout
    assert "rule reporting" in result.stdout


def test_snakemake_placeholder_workflow_execution():
    """Integration test confirming placeholder Snakemake workflow executes."""

    output_dir = Path("tests/fixtures/outputs/test_job")

    if output_dir.exists():
        shutil.rmtree(output_dir)

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

    report_path = output_dir / "reporting" / "sample_001.report.md"

    assert result.returncode == 0
    assert report_path.exists()
    assert "Report for sample_001" in report_path.read_text()