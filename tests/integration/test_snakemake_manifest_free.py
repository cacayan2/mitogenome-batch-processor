"""test_snakemake_manifest_free.py

Integration test for manifest-free workflow initialization.
"""

# Imports
from pathlib import Path
import shutil
import subprocess

import pandas as pd
import pytest


pytestmark = pytest.mark.slow


def test_snakemake_manifest_free_dry_run():
    """Confirm Snakemake discovers FASTQs and builds its DAG."""
    output_directory = Path(
        "tests/fixtures/outputs/test_job"
    )

    runtime_manifest = (
        output_directory
        / "metadata"
        / "runtime_manifest.tsv"
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
                (
                    "tests/fixtures/config/"
                    "config.manifest_free.yaml"
                ),
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

        assert "Building DAG of jobs" in result.stdout

        assert runtime_manifest.exists()

        table = pd.read_csv(
            runtime_manifest,
            sep="\t",
        )

        assert table[
            "sample_id"
        ].tolist() == [
            "lemon_shark_001",
        ]

        assert table.loc[
            0,
            "r1",
        ].endswith(
            "lemon_shark_001_R1.fastq.gz"
        )

        assert table.loc[
            0,
            "r2",
        ].endswith(
            "lemon_shark_001_R2.fastq.gz"
        )

    finally:
        if output_directory.exists():
            shutil.rmtree(
                output_directory
            )