"""test_blast_exec.py

Integration tests for the BLAST execution layer through Snakemake.
"""

# Imports
from pathlib import Path
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.slow


def test_blast_exec_layer_through_snakemake_real_assembly():
    """Integration test confirming Snakemake executes BLAST on an assembly."""

    # Defining sample and job paths.
    sample_id = "common_carp_001"
    output_dir = Path("tests/fixtures/outputs/test_job")

    # Defining upstream assembly paths.
    assembly_fasta = (
        output_dir
        / "assembly"
        / f"{sample_id}.fasta"
    )
    assembly_done = (
        output_dir
        / "assembly"
        / f"{sample_id}.assembly.done"
    )

    # Defining BLAST database paths.
    database_prefix = Path(
        "tests/fixtures/blast/database/test_mito"
    )
    database_done = (
        output_dir
        / "setup"
        / "blast"
        / "blast_database.done"
    )
    database_metadata = (
        output_dir
        / "setup"
        / "blast"
        / "blast_database.metadata.json"
    )

    # Defining BLAST output paths.
    blast_dir = (
        output_dir
        / "phylogeny"
        / "blast"
    )
    blast_results = (
        blast_dir
        / f"{sample_id}.blast.tsv"
    )
    blast_done = (
        blast_dir
        / f"{sample_id}.blast.done"
    )
    log_file = (
        output_dir
        / "logs"
        / "blast"
        / f"{sample_id}.log"
    )

    # Removing previous BLAST outputs.
    if blast_results.exists():
        blast_results.unlink()

    if blast_done.exists():
        blast_done.unlink()

    if log_file.exists():
        log_file.unlink()

    # Removing prior database setup marker.
    if database_done.exists():
        database_done.unlink()

    if database_metadata.exists():
        database_metadata.unlink()

    # Removing previous test database components.
    for database_file in database_prefix.parent.glob(
        f"{database_prefix.name}.*"
    ):
        if database_file.is_file():
            database_file.unlink()

    try:
        # Confirming assembly exists so this test does not rerun assembly.
        assert assembly_fasta.exists()
        assert assembly_done.exists()

        # Running BLAST validation through Snakemake.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config_blast_real.yaml",
                "--use-conda",
                "--cores",
                "4",
                str(blast_done),
            ],
            capture_output=True,
            text=True,
        )

        # Checking Snakemake execution.
        assert result.returncode == 0, result.stdout + result.stderr

        # Checking BLAST execution outputs.
        assert blast_done.exists()
        assert blast_results.exists()
        assert blast_results.is_file()
        assert log_file.exists()

        # Checking database setup outputs.
        assert database_done.exists()
        assert database_metadata.exists()

        # Checking required BLAST database components.
        assert Path(f"{database_prefix}.nhr").exists()
        assert Path(f"{database_prefix}.nin").exists()
        assert Path(f"{database_prefix}.nsq").exists()

        # Confirming BLAST produced at least one hit.
        result_lines = [
            line
            for line in blast_results.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        assert len(result_lines) >= 1

        # Confirming output contains the expected query identifier.
        first_result = result_lines[0].split("\t")

        # Reading the actual query FASTA identifier.
        query_header = next(
            line
            for line in assembly_fasta.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.startswith(">")
        )

        expected_query_id = query_header[1:].split()[0]

        # Confirming BLAST reports the query FASTA identifier.
        assert first_result[0] == expected_query_id

        # Confirming basic alignment values are valid.
        assert first_result[1]
        assert 0 < float(first_result[2]) <= 100
        assert int(first_result[3]) > 0
        assert float(first_result[10]) >= 0
        assert float(first_result[11]) > 0

    finally:
        # Leave outputs available for inspection while BLAST integration stabilizes.
        pass