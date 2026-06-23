"""test_fastp_exec.py

Integration tests for the fastp execution layer through Snakemake.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow

def test_fastp_exec_layer_through_snakemake():
    """Integration test confirming Snakemake executes fastp through run_fastp.py."""

    # Defining test paths.
    output_dir = Path("tests/fixtures/outputs/test_job")
    trimming_dir = output_dir / "trimming"
    log_file = output_dir / "logs" / "trimming" / "sample_001.log"
    target = trimming_dir / "sample_001_R1.trimmed.fastq.gz"

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Running the fastp trimming rule through Snakemake.
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
        assert (trimming_dir / "sample_001_R2.trimmed.fastq.gz").exists()
        assert (trimming_dir / "sample_001.fastp.html").exists()
        assert (trimming_dir / "sample_001.fastp.json").exists()
        assert log_file.exists()

    finally:
        # Cleanup.
        if output_dir.exists():
            shutil.rmtree(output_dir)