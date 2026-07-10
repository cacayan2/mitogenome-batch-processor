"""Parser for extracting assembly statistics from FASTA output."""

from __future__ import annotations

import logging
from pathlib import Path

from mitopipeline.models.assembly_stats import AssemblyStats


def parse_fasta_sequences(
    fasta_path: Path,
    logger: logging.Logger | None = None,
) -> dict[str, str]:
    """Parse a FASTA file and return sequence strings keyed by identifier."""
    if logger is not None:
        logger.info("Parsing FASTA file %s.", fasta_path)

    sequences: dict[str, list[str]] = {}
    current_id: str | None = None

    with fasta_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            if line.startswith(">"):
                current_id = line[1:].split()[0]
                sequences[current_id] = []
            else:
                if current_id is None:
                    raise ValueError(
                        f"No header found in FASTA file {fasta_path}."
                    )
                sequences[current_id].append(line.upper())

    if logger is not None:
        logger.info(
            "Parsed %d sequences from FASTA file %s.",
            len(sequences),
            fasta_path,
        )
    return {
        sequence_id: "".join(parts)
        for sequence_id, parts in sequences.items()
    }


def calculate_gc_content_percent(
    sequence: str,
    logger: logging.Logger | None = None,
) -> float:
    """Calculate GC content as a percentage, ignoring ambiguous bases."""
    bases = [
        base
        for base in sequence.upper()
        if base in {"A", "C", "G", "T"}
    ]
    if not bases:
        if logger is not None:
            logger.error("No canonical bases found in sequence.")
        return 0.0

    gc_count = sum(base in {"G", "C"} for base in bases)
    return round((gc_count / len(bases)) * 100, 2)


def infer_circularization_status(
    fasta_path: Path,
    logger: logging.Logger | None = None,
) -> str | None:
    """Infer circularization from FASTA headers, then filename conventions."""
    if logger is not None:
        logger.info(
            "Inferring circularization status for FASTA file %s.",
            fasta_path,
        )

    # GetOrganelle stores status in headers such as >3185-(circular).
    # MitoPipeline normalizes the output filename to data.fasta, so the
    # header is the primary source of truth.
    with fasta_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if not line.startswith(">"):
                break

            header = line[1:].lower()
            if "circular" in header or "complete" in header:
                if logger is not None:
                    logger.info(
                        "FASTA header indicates a circular assembly: %s",
                        line,
                    )
                return "complete"
            if "linear" in header or "scaffold" in header:
                if logger is not None:
                    logger.info(
                        "FASTA header indicates an incomplete assembly: %s",
                        line,
                    )
                return "incomplete"

    # Backward-compatible fallback for native GetOrganelle filenames.
    name = fasta_path.name.lower()
    if "complete" in name or "circular" in name:
        return "complete"
    if "scaffold" in name or "linear" in name:
        return "incomplete"

    if logger is not None:
        logger.warning(
            "Could not infer circularization status for FASTA file %s.",
            fasta_path,
        )
    return None


def parse_assembly_stats(
    sample_id: str,
    fasta_path: Path,
    runtime_seconds: float | None = None,
    logger: logging.Logger | None = None,
) -> AssemblyStats:
    """Parse assembly statistics from a FASTA file."""
    if logger is not None:
        logger.info("Parsing assembly stats for sample %s.", sample_id)

    fasta_path = Path(fasta_path)
    if not fasta_path.exists() or not fasta_path.is_file():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    sequences = parse_fasta_sequences(fasta_path, logger)
    if not sequences:
        raise ValueError(f"No sequences found in FASTA file {fasta_path}.")

    total_sequence = "".join(sequences.values())
    return AssemblyStats(
        sample_id=sample_id,
        fasta_path=fasta_path,
        contig_count=len(sequences),
        total_length_bp=sum(len(sequence) for sequence in sequences.values()),
        gc_content_percent=calculate_gc_content_percent(
            total_sequence,
            logger,
        ),
        circularization_status=infer_circularization_status(
            fasta_path,
            logger,
        ),
        runtime_seconds=runtime_seconds,
    )
