"""test_fastqc_raw_exec.py

Integration tests for the FastQC execution layer through Snakemake, specifically for raw FASTQ reads.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_fastqc_raw_exec_layer_through_snakemake():
    """Integration test confirming Snakemake executes raw FastQC through run_fastqc_raw.py."""

    # Defining test paths.
    output_dir = Path("tests/fixtures/outputs/test_job")
    qc_dir = output_dir / "qc" / "raw"
    log_file = output_dir / "logs" / "fastqc" / "sample_001.raw.log"
    target = qc_dir / "sample_001_R1_fastqc.html"

    try:
        # Running the raw FastQC rule through Snakemake.
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
        assert result.returncode == 0, result.stdout + result.stderr
        assert target.exists()
        assert (qc_dir / "sample_001_R1_fastqc.zip").exists()
        assert (qc_dir / "sample_001_R2_fastqc.html").exists()
        assert (qc_dir / "sample_001_R2_fastqc.zip").exists()
        assert (qc_dir / "sample_001.qc.raw.done").exists()
        assert log_file.exists()

    finally:
        pass