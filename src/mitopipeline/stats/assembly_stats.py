"""assembly_stats.py

This module contains the parser for extracting assembly data.
"""

# Imports
from pathlib import Path
import logging
from mitopipeline.models.assembly_stats import AssemblyStats
from mitopipeline.logging.logger_factory import make_logger

def parse_fasta_sequences(fasta_path: Path, logger: logging.Logger | None = None) -> dict[str, str]:
    """Parses a FASTA file and returns a dictionary of sequences.

    Args:
        fasta_path (Path): The path to the FASTA file.

    Returns:
        dict[str, str]: A dictionary of sequences.
    """
    # Logging if logger is not None. 
    if logger is not None: logger.info(f"Parsing FASTA file {fasta_path}.")

    # Creating empty data structures. 
    sequences: dict[str, list[str]] = {}
    current_id: str | None = None

    with fasta_path.open("r", encoding="utf-8") as handle:
        # Iterating over lines.
        for line in handle:
            # Stripping leading and trailing whitespace.
            line = line.strip()

            # Skipping empty lines.
            if not line:
                continue

            # Checking for header.
            if line.startswith(">"):
                current_id = line[1:].split()[0]
                sequences[current_id] = []
            else:
                if current_id is None:
                    if logger is not None: logger.error(f"No header found in FASTA file {fasta_path}.")
                    raise ValueError(f"No header found in FASTA file {fasta_path}.")
                sequences[current_id].append(line.upper())

    # Returning sequences.
    if logger is not None: logger.info(f"Parsed {len(sequences)} sequences from FASTA file {fasta_path}.")
    return {seq_id: "".join(parts) for seq_id, parts in sequences.items()}

def calculate_gc_content_percent(sequence: str, logger: logging.Logger | None = None) -> float: 
    """Calculates the GC content percentage of a sequence.

    Args:
        sequence (str): The sequence to calculate GC content for.

    Returns:
        float: The GC content percentage.
    """
    # Obtaining bases.
    bases = [base for base in sequence.upper() if base in {"A", "C", "G", "T"}]

    # Returning 0 if bases is empty.
    if len(bases) == 0:
        if logger is not None: logger.error(f"No bases found in sequence {sequence}.")
        return 0.0
    
    # Obtaining the GC content and returning.
    gc_count = sum(1 for base in bases if base in {"G", "C"})
    return round((gc_count / len(bases)) * 100, 2)

def infer_circularization_status(fasta_path: Path, logger: logging.Logger | None = None) -> str | None:
    """Infers the circularization status of a FASTA file.

    Args:
        fasta_path (Path): The path to the FASTA file.
        logger (logging.Logger | None, optional): The logger to use. Defaults to None.

    Returns:
        str | None: The inferred circularization status or None if not circularized.
    """
    # Logging if logger is not None.
    if logger is not None: logger.info(f"Inferring circularization status for FASTA file {fasta_path}.")

    # Obtaining the name of the FASTA file.
    name = fasta_path.name.lower()

    # Inferring circularization status.
    if "complete" in name or "circular" in name:
        if logger is not None: logger.info(f"FASTA file {fasta_path} is circular.")
        return "complete"
    if "scaffold" in name or "linear" in name:
        if logger is not None: logger.info(f"FASTA file {fasta_path} is not circularized.")
        return "incomplete"
    
    # Returning None.
    if logger is not None: logger.error(f"Could not infer circularization status for FASTA file {fasta_path}.")
    return None

def parse_assembly_stats(
        sample_id: str,
        fasta_path: Path,
        runtime_seconds: float | None = None,
        logger: logging.Logger | None = None
        ) -> AssemblyStats:
    """Parses assembly stats from a FASTA file and returns an AssemblyStats object.

    Args:
        sample_id (str): The sample id.
        fasta_path (Path): The path to the FASTA file.
        runtime_seconds (float | None, optional): The runtime in seconds. Defaults to None.

    Returns:
        AssemblyStats: An AssemblyStats object.
    """
    # Logging if logger is not None.
    if logger is not None: logger.info(f"Parsing assembly stats for sample {sample_id}.")

    # Verifying the fasta path exists.
    if not fasta_path.exists() or not fasta_path.is_file():
        if logger is not None: logger.error(f"FASTA file not found: {fasta_path}")
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
    
    # Parsing the Fasta file.
    sequences = parse_fasta_sequences(fasta_path, logger)

    # Verifying that sequences are present in the Fasta file.
    if len(sequences) == 0:
        if logger is not None: logger.error(f"No sequences found in FASTA file {fasta_path}.")
        raise ValueError(f"No sequences found in FASTA file {fasta_path}.")
    
    # Joining the total sequence.
    total_sequence = "".join(sequences.values())

    # Returning the AssemblyStats object.
    return AssemblyStats(
        sample_id = sample_id,
        fasta_path = fasta_path,
        contig_count = len(sequences),
        total_length_bp = sum(len(sequence) for sequence in sequences.values()),
        gc_content_percent = calculate_gc_content_percent(total_sequence, logger),
        circularization_status = infer_circularization_status(fasta_path, logger),
        runtime_seconds = runtime_seconds,
    )
