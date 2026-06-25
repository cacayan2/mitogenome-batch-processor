"""test_getorganelle_exec.py

Integration tests for the GetOrganelle execution layer through Snakemake.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_getorganelle_exec_layer_through_snakemake():
    """Integration test confirming Snakemake executes GetOrganelle through run_getorganelle.py."""

    # Defining test paths.
    output_dir = Path("tests/fixtures/outputs/test_job")
    assembly_dir = output_dir / "assembly"
    log_file = output_dir / "logs" / "assembly" / "sample_001.log"
    target = assembly_dir / "sample_001.fasta"

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Running the GetOrganelle assembly rule through Snakemake.
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
        assert (assembly_dir / "sample_001.gfa").exists()
        assert (assembly_dir / "sample_001.assembly.done").exists()
        assert log_file.exists()

    finally:
        # Cleanup.
        pass