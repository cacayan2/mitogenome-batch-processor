"""test_stage_selection.py

Integration tests for configurable Snakemake stage selection.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_qc_raw_only_stage_selection():
    """Test that enabling only raw QC builds only the raw QC DAG."""

    output_dir = Path("tests/fixtures/outputs/test_job")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config_qc_raw_only.yaml",
                "--dry-run",
                "--cores",
                "1",
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        assert result.returncode == 0, output
        assert "rule qc_raw" in output
        assert "rule trimming" not in output
        assert "rule qc_trimmed" not in output
        assert "rule assembly" not in output
        assert "rule annotation" not in output
        assert "rule phylogeny" not in output
        assert "rule reporting" not in output

    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_preprocessing_only_stage_selection():
    """Test that preprocessing stages build without assembly."""

    output_dir = Path("tests/fixtures/outputs/test_job")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config_preprocessing_only.yaml",
                "--dry-run",
                "--cores",
                "1",
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        assert result.returncode == 0, output
        assert "rule qc_raw" in output
        assert "rule trimming" in output
        assert "rule qc_trimmed" in output
        assert "rule assembly" not in output
        assert "rule annotation" not in output
        assert "rule phylogeny" not in output
        assert "rule reporting" not in output

    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)