"""Functions for generating combined phylogenetic FASTA datasets."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Callable, TextIO

from Bio import Entrez, SeqIO
from Bio.SeqRecord import SeqRecord


def parse_top_blast_hits(
    top_hits_path: str | Path,
    logger: logging.Logger | None = None,
) -> list[dict]:
    """Parse selected BLAST hits from a TSV file and order them by rank."""
    top_hits_path = Path(top_hits_path)

    if not top_hits_path.exists():
        raise FileNotFoundError(f"Top BLAST-hit file not found: {top_hits_path}")
    if not top_hits_path.is_file():
        raise ValueError(f"Top BLAST-hit file is not a file: {top_hits_path}")

    with top_hits_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"Top BLAST-hit file is empty: {top_hits_path}")

        required_columns = {"rank", "sseqid", "sscinames"}
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            missing_text = ",".join(sorted(missing_columns))
            raise ValueError(
                "Top BLAST-hit file is missing required columns: "
                f"{missing_text}"
            )

        matches: list[dict] = []
        for line_number, row in enumerate(reader, start=2):
            if not row or all(str(value).strip() == "" for value in row.values()):
                continue
            try:
                row["rank"] = int(row["rank"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid rank on line {line_number} of "
                    f"{top_hits_path}: {row.get('rank')}"
                ) from error
            matches.append(row)

    if not matches:
        raise ValueError(f"No selected BLAST hits found in {top_hits_path}")

    matches.sort(key=lambda match: match["rank"])
    if logger is not None:
        logger.info(
            "Parsed %d selected BLAST hits from %s.",
            len(matches),
            top_hits_path,
        )
    return matches


def normalize_blast_accession(
    subject_id: str,
    logger: logging.Logger | None = None,
) -> str:
    """Extract a nucleotide accession from a BLAST subject identifier."""
    subject_id = subject_id.strip()
    if not subject_id:
        raise ValueError("BLAST subject identifier cannot be empty.")

    parts = [part.strip() for part in subject_id.split("|") if part.strip()]
    database_prefixes = {"ref", "gb", "emb", "dbj", "tpg", "tpe", "tpd"}

    if len(parts) >= 2 and parts[0].lower() in database_prefixes:
        accession = parts[1]
    else:
        accession = parts[0]

    if not accession:
        raise ValueError(
            "Could not extract accession from BLAST subject identifier: "
            f"{subject_id}."
        )
    return accession


def scientific_name_is_missing(value: object) -> bool:
    """Return whether a scientific name is absent or a placeholder."""
    return str(value or "").strip().lower() in {
        "",
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
        "unknown_species",
        "not available",
    }


def infer_scientific_name_from_record(
    record: SeqRecord,
    accession: str,
) -> str:
    """Infer a scientific name from NCBI record metadata or description."""
    organism = str(record.annotations.get("organism", "")).strip()
    if not scientific_name_is_missing(organism):
        return organism

    description = record.description.strip()
    if description.startswith(accession):
        description = description[len(accession):].strip()

    match = re.match(
        r"^([A-Z][A-Za-z.-]+)\s+([a-z][A-Za-z.-]+)",
        description,
    )
    if match is None:
        return "unknown_species"

    return f"{match.group(1)} {match.group(2)}"


def standardize_sequence_name(value: str) -> str:
    """Standardize text for safe use in a FASTA identifier."""
    value = value.strip()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^a-zA-Z0-9_.-]", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.strip("_")
    return value or "unknown"


def build_assembled_sequence_name(sample_id: str) -> str:
    """Build the standardized assembled-genome identifier."""
    return f"{standardize_sequence_name(sample_id)}|assembled"


def build_reference_sequence_name(
    rank: int,
    accession: str,
    scientific_name: str,
) -> str:
    """Build a readable, unique reference identifier for tree tips."""
    del rank
    standardized_accession = standardize_sequence_name(accession)
    standardized_name = standardize_sequence_name(scientific_name)

    return f"{standardized_name}__{standardized_accession}"


def read_assembled_genome(
    assembly_fasta: str | Path,
    sample_id: str,
    logger: logging.Logger | None = None,
) -> SeqRecord:
    """Read and standardize one assembled mitochondrial genome."""
    assembly_fasta = Path(assembly_fasta)
    if not assembly_fasta.exists():
        raise FileNotFoundError(
            f"Assembly FASTA not found: {assembly_fasta}."
        )
    if not assembly_fasta.is_file():
        raise ValueError(
            f"Assembly FASTA path is not a file: {assembly_fasta}."
        )

    records = list(SeqIO.parse(assembly_fasta, "fasta"))
    if not records:
        raise ValueError(
            f"No sequences found in assembly FASTA: {assembly_fasta}."
        )
    if len(records) != 1:
        raise ValueError(
            "Expected exactly one assembled mitochondrial sequence in "
            f"{assembly_fasta}, but found {len(records)}."
        )

    record = records[0]
    if len(record.seq) == 0:
        raise ValueError(f"Assembly sequence is empty: {assembly_fasta}.")

    record.id = build_assembled_sequence_name(sample_id)
    record.name = record.id
    record.description = ""

    if logger is not None:
        logger.info(
            "Read assembled genome containing %d bases from %s.",
            len(record.seq),
            assembly_fasta,
        )
    return record


def retrieve_reference_sequences(
    accessions: list[str],
    entrez_email: str,
    entrez_api_key: str | None = None,
    logger: logging.Logger | None = None,
    efetch: Callable[..., TextIO] | None = None,
) -> list[SeqRecord]:
    """Retrieve nucleotide reference sequences from NCBI Entrez."""
    if not accessions:
        raise ValueError("At least one accession is required.")
    if not entrez_email.strip():
        raise ValueError("An Entrez email address is required.")

    Entrez.email = entrez_email.strip()
    Entrez.api_key = entrez_api_key.strip() if entrez_api_key else None
    if efetch is None:
        efetch = Entrez.efetch

    if logger is not None:
        logger.info(
            "Retrieving %d reference sequences from NCBI.",
            len(accessions),
        )

    with efetch(
        db="nucleotide",
        id=",".join(accessions),
        rettype="fasta",
        retmode="text",
    ) as handle:
        records = list(SeqIO.parse(handle, "fasta"))

    if logger is not None:
        logger.info(
            "Retrieved %d reference sequences from NCBI.",
            len(records),
        )
    return records


def order_and_standardize_reference_sequences(
    matches: list[dict],
    retrieved_records: list[SeqRecord],
    logger: logging.Logger | None = None,
) -> list[SeqRecord]:
    """Order retrieved records by BLAST rank and assign readable names."""
    records_by_accession: dict[str, SeqRecord] = {}
    for record in retrieved_records:
        full_accession = record.id
        records_by_accession[full_accession] = record
        records_by_accession[full_accession.split(".")[0]] = record

    ordered_records: list[SeqRecord] = []
    for match in matches:
        accession = normalize_blast_accession(match["sseqid"])
        record = records_by_accession.get(accession)
        if record is None:
            record = records_by_accession.get(accession.split(".")[0])
        if record is None:
            raise ValueError(
                "NCBI did not return the expected reference sequence: "
                f"{accession}."
            )

        record = record[:]
        scientific_name = str(match.get("sscinames") or "").strip()
        if scientific_name_is_missing(scientific_name):
            scientific_name = infer_scientific_name_from_record(
                record=record,
                accession=accession,
            )
        record.id = build_reference_sequence_name(
            rank=match["rank"],
            accession=accession,
            scientific_name=scientific_name,
        )
        record.name = record.id
        record.description = ""

        if len(record.seq) == 0:
            raise ValueError(
                f"Retrieved reference sequence is empty: {accession}."
            )
        ordered_records.append(record)

    if logger is not None:
        logger.info(
            "Ordered and standardized %d reference sequences.",
            len(ordered_records),
        )
    return ordered_records


def validate_alignment_dataset(
    records: list[SeqRecord],
    expected_reference_count: int,
) -> None:
    """Validate combined phylogenetic records before writing FASTA."""
    expected_total = expected_reference_count + 1
    if len(records) != expected_total:
        raise ValueError(
            f"Expected {expected_total} total sequences but found "
            f"{len(records)}."
        )
    if not records[0].id.endswith("|assembled"):
        raise ValueError("The assembled genome must be the first record.")

    identifiers = [record.id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate sequence identifiers were generated.")

    for record in records:
        if len(record.seq) == 0:
            raise ValueError(f"Sequence is empty: {record.id}.")


def generate_alignment_dataset(
    sample_id: str,
    assembly_fasta: str | Path,
    top_hits_tsv: str | Path,
    output_fasta: str | Path,
    entrez_email: str,
    entrez_api_key: str | None = None,
    logger: logging.Logger | None = None,
    retrieve_function: Callable[..., list[SeqRecord]] | None = None,
) -> None:
    """Generate the combined unaligned phylogenetic FASTA dataset."""
    output_fasta = Path(output_fasta)
    if retrieve_function is None:
        retrieve_function = retrieve_reference_sequences

    assembly_record = read_assembled_genome(
        assembly_fasta=assembly_fasta,
        sample_id=sample_id,
        logger=logger,
    )
    matches = parse_top_blast_hits(top_hits_tsv, logger=logger)
    accessions = [
        normalize_blast_accession(match["sseqid"])
        for match in matches
    ]
    retrieved_records = retrieve_function(
        accessions=accessions,
        entrez_email=entrez_email,
        entrez_api_key=entrez_api_key,
        logger=logger,
    )
    reference_records = order_and_standardize_reference_sequences(
        matches=matches,
        retrieved_records=retrieved_records,
        logger=logger,
    )

    combined_records = [assembly_record, *reference_records]
    validate_alignment_dataset(
        records=combined_records,
        expected_reference_count=len(matches),
    )

    output_fasta.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write(combined_records, output_fasta, "fasta")

    if logger is not None:
        logger.info(
            "Wrote %d sequences to %s.",
            len(combined_records),
            output_fasta,
        )
