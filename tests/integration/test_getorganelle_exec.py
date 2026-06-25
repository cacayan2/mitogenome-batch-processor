"""test_getorganelle_exec.py

Integration tests for the GetOrganelle execution layer through Snakemake.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_getorganelle_exec_layer_through_snakemake_real_data():
    """Integration test confirming Snakemake executes GetOrganelle on real fixture data."""

    # Defining test paths.
    sample_id = "common_carp_001"
    output_dir = Path("tests/fixtures/outputs/test_job")
    assembly_dir = output_dir / "assembly"
    log_file = output_dir / "logs" / "assembly" / f"{sample_id}.log"
    target = assembly_dir / f"{sample_id}.assembly.done"

    try:
        # Running the GetOrganelle assembly rule through Snakemake.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config_getorganelle_real.yaml",
                "--use-conda",
                "--cores",
                "20",
                str(target),
            ],
            capture_output=True,
            text=True,
        )

        # Assert statements.
        assert result.returncode == 0, result.stdout + result.stderr
        assert target.exists()
        assert log_file.exists()
        assert assembly_dir.exists()

        # Temporary exploratory assertions.
        # Keep these until we know exactly what GetOrganelle produces.
        assembly_files = list(assembly_dir.rglob("*"))
        assert len(assembly_files) > 0

    finally:
        # Leave outputs for inspection until output normalization is implemented.
        pass