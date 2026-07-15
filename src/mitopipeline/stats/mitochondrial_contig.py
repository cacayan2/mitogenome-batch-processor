"""Functions for selecting a mitochondrial assembly contig."""

from __future__ import annotations

import csv
from pathlib import Path

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


def read_blast_query_ids(top_hits_tsv: str | Path) -> set[str]:
    """Read the unique BLAST query IDs represented by selected hits."""
    top_hits_tsv = Path(top_hits_tsv)

    if not top_hits_tsv.is_file():
        raise FileNotFoundError(
            f"Top-hit TSV file not found: {top_hits_tsv}"
        )

    with top_hits_tsv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")

        if reader.fieldnames is None:
            raise ValueError(f"Top-hit TSV is empty: {top_hits_tsv}")

        if "qseqid" not in reader.fieldnames:
            raise ValueError(
                f"Top-hit TSV is missing required column qseqid: "
                f"{top_hits_tsv}"
            )

        query_ids = {
            row["qseqid"].strip()
            for row in reader
            if row.get("qseqid", "").strip()
        }

    if not query_ids:
        raise ValueError(
            f"No BLAST query IDs were found in {top_hits_tsv}"
        )

    return query_ids


def select_mitochondrial_contig(
    assembly_fasta: str | Path,
    top_hits_tsv: str | Path,
    output_fasta: str | Path,
) -> SeqRecord:
    """Select the assembly contig represented by the selected BLAST hits."""
    assembly_fasta = Path(assembly_fasta)
    output_fasta = Path(output_fasta)

    if not assembly_fasta.is_file():
        raise FileNotFoundError(
            f"Assembly FASTA file not found: {assembly_fasta}"
        )

    query_ids = read_blast_query_ids(top_hits_tsv)

    if len(query_ids) != 1:
        raise ValueError(
            "Selected BLAST hits refer to multiple assembly contigs: "
            f"{sorted(query_ids)}"
        )

    selected_id = next(iter(query_ids))

    matching_records = [
        record
        for record in SeqIO.parse(assembly_fasta, "fasta")
        if record.id == selected_id
    ]

    if len(matching_records) != 1:
        raise ValueError(
            f"Expected exactly one assembly contig named {selected_id}, "
            f"but found {len(matching_records)} in {assembly_fasta}"
        )

    selected_record = matching_records[0]

    if len(selected_record.seq) == 0:
        raise ValueError(
            f"Selected assembly contig is empty: {selected_id}"
        )

    output_fasta.parent.mkdir(parents=True, exist_ok=True)

    records_written = SeqIO.write(
        [selected_record],
        output_fasta,
        "fasta",
    )

    if records_written != 1:
        raise RuntimeError(
            f"Expected to write one sequence but wrote {records_written}"
        )

    return selected_record