"""test_fastqc_exec.py

Integration tests for the FastQC execution layer through Snakemake, specifically for raw FASTQ reads.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_fastqc_exec_layer_through_snakemake():
    """Integration test confirming Snakemake executes FastQC through run_fastqc.py."""

    # Defining test paths.
    output_dir = Path("tests/fixtures/outputs/test_job")
    target = output_dir / "qc" / "sample_001_R1_fastqc.html"
    log_file = output_dir / "logs" / "fastqc" / "sample_001.log"

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Running the FastQC rule through Snakemake.
    result = subprocess.run(
        [
            "snakemake",
            "-s",
            "ctrl/Snakefile",
            "--configfile",
            "tests/fixtures/config/config.yaml",
            "--use-conda",
            "--cores",
            "1",
            str(target),
        ],
        capture_output=True,
        text=True,
    )

    # Assert statements.
    assert result.returncode == 0
    assert target.exists()
    assert (output_dir / "qc_raw" / "sample_001_R1_fastqc.zip").exists()
    assert (output_dir / "qc_raw" / "sample_001_R1_fastqc.html").exists()
    assert (output_dir / "qc_raw" / "sample_001_R2_fastqc.html").exists()
    assert (output_dir / "qc_raw" / "sample_001_R2_fastqc.zip").exists()
    assert log_file.exists()

    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)