"""test_blast_hits_exec.py

Integration tests for top BLAST match selection through Snakemake.
"""

# Imports
import csv
from pathlib import Path
import subprocess

import pytest


pytestmark = pytest.mark.slow


def test_blast_hit_selection_through_snakemake():
    """Integration test confirming Snakemake selects top BLAST matches."""

    # Defining sample and job paths.
    sample_id = "common_carp_001"
    output_dir = Path("tests/fixtures/outputs/test_job")

    # Defining required assembly paths.
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

    # Defining deterministic BLAST reference input.
    reference_fasta = Path(
        "tests/fixtures/blast/reference_mitogenomes.fasta"
    )

    # Defining database paths.
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

    # Defining BLAST outputs.
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

    # Defining top-hit outputs.
    top_hits = (
        blast_dir
        / f"{sample_id}.top_hits.tsv"
    )
    top_hits_done = (
        blast_dir
        / f"{sample_id}.top_hits.done"
    )
    log_file = (
        output_dir
        / "logs"
        / "blast_hits"
        / f"{sample_id}.log"
    )

    # Confirming the upstream assembly fixture exists.
    assert assembly_fasta.exists()
    assert assembly_done.exists()

    # Creating a deterministic reference FASTA from the query assembly.
    assembly_lines = assembly_fasta.read_text(
        encoding="utf-8"
    ).splitlines()

    assert assembly_lines
    assert assembly_lines[0].startswith(">")

    assembly_lines[0] = ">common_carp_reference"

    reference_fasta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    reference_fasta.write_text(
        "\n".join(assembly_lines) + "\n",
        encoding="utf-8",
    )

    # Removing prior top-hit outputs.
    for path in (
        top_hits,
        top_hits_done,
        log_file,
    ):
        if path.exists():
            path.unlink()

    # Removing prior BLAST outputs so the full branch is exercised.
    for path in (
        blast_results,
        blast_done,
        database_done,
        database_metadata,
    ):
        if path.exists():
            path.unlink()

    # Removing prior database components.
    database_prefix.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    for database_file in database_prefix.parent.glob(
        f"{database_prefix.name}.*"
    ):
        if database_file.is_file():
            database_file.unlink()

    # Running the complete BLAST and hit-selection branch.
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
            str(top_hits_done),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    # Confirming database setup outputs.
    assert database_done.exists()
    assert database_metadata.exists()
    assert Path(f"{database_prefix}.nhr").exists()
    assert Path(f"{database_prefix}.nin").exists()
    assert Path(f"{database_prefix}.nsq").exists()

    # Confirming BLAST execution outputs.
    assert blast_results.exists()
    assert blast_results.is_file()
    assert blast_done.exists()

    # Confirming hit-selection outputs.
    assert top_hits.exists()
    assert top_hits.is_file()
    assert top_hits_done.exists()
    assert log_file.exists()

    # Reading selected matches.
    with top_hits.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    # Confirming up to six matches were selected.
    assert 1 <= len(rows) <= 6

    # Confirming sequential ranking.
    assert [int(row["rank"]) for row in rows] == list(
        range(1, len(rows) + 1)
    )

    # Confirming pipeline sample metadata.
    assert all(
        row["sample_id"] == sample_id
        for row in rows
    )

    # Confirming accessions are unique and usable for retrieval.
    subject_ids = [row["sseqid"] for row in rows]

    assert all(subject_ids)
    assert len(subject_ids) == len(set(subject_ids))

    # Confirming required BLAST metadata.
    for row in rows:
        assert row["qseqid"]
        assert row["sseqid"]
        assert 0 < float(row["pident"]) <= 100
        assert int(row["length"]) > 0
        assert float(row["evalue"]) >= 0
        assert float(row["bitscore"]) > 0
        assert 0 <= float(row["qcovs"]) <= 100

    # Confirming rows follow the parser's complete ranking key.
    observed_ranking = [
        (
            float(row["evalue"]),
            -float(row["bitscore"]),
            -float(row["qcovs"]),
            -float(row["pident"]),
            -int(row["length"]),
            row["sseqid"],
        )
        for row in rows
    ]

    assert observed_ranking == sorted(observed_ranking)