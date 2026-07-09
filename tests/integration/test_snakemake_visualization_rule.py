"""test_snakemake_visualization_rule.py

Integration test confirming the visualization rule is present in the DAG.
"""

# Imports
from pathlib import Path
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.slow


def test_snakemake_visualization_dry_run():
    """Confirm Snakemake can schedule visualization outputs."""
    output_directory = Path(
        "tests/fixtures/outputs/test_job"
    )

    if output_directory.exists():
        shutil.rmtree(
            output_directory
        )

    try:
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

        assert result.returncode == 0, (
            result.stdout
            + result.stderr
        )

        if "visualization: true" in Path(
            "tests/fixtures/config/config.yaml"
        ).read_text(
            encoding="utf-8"
        ):
            assert "rule circular_genome_map" in result.stdout

    finally:
        if output_directory.exists():
            shutil.rmtree(
                output_directory
            )
