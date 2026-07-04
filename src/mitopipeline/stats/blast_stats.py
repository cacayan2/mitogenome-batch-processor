"""blast_stats.py

Parse and rank BLAST matches for phylogenetic variations.
"""

# Imports
import csv
from logging import Logger
from pathlib import Path

# Constants
BLAST_COLUMNS = [
    "qseqid",
    "sseqid",
    "pident",
    "length",
    "mismatch",
    "gapopen",
    "qstart",
    "qend",
    "sstart",
    "send",
    "evalue",
    "bitscore",
    "qcovs",
    "staxids",
    "sscinames",
    "stitle",
]

INTEGER_COLUMNS = {
    "length",
    "mismatch",
    "gapopen",
    "qstart",
    "qend",
    "sstart",
    "send",
}

FLOAT_COLUMNS = {
    "pident",
    "evalue",
    "bitscore",
    "qcovs",
}

def parse_blast_tsv(
        blast_path: str | Path,
        logger: Logger | None = None
) -> list[dict]:
    """Parse tabular BLAST output.
    
    Args:
        blast_path (str | Path): Path to tabular BLAST output.
        logger (Logger | None, optional): Logger to use. Defaults to None.
    
    Returns:
        list[dict]: List of BLAST matches.
    """
    # Normalizing blast path.
    blast_path = Path(blast_path)

    # Verifying that path exists and is a file.
    if not blast_path.exists():
        if logger is not None: logger.error(f"File {blast_path} not found.")
        raise FileNotFoundError(f"File {blast_path} not found.")
    if not blast_path.is_file():
        if logger is not None: logger.error(f"File {blast_path} is not a file.")
        raise ValueError(f"File {blast_path} is not a file.")

    # Initializing empty matches list and parsing blast data.
    matches = []
    with blast_path.open("r", encoding = "utf-8", errors = "replace", newline = "") as handle:
        reader = csv.reader(handle, delimiter = "\t")
        for line_number, row in enumerate (reader, start = 1):
            if not row or all(value.strip() == "" for value in row):
                continue
            if len(row) != len(BLAST_COLUMNS):
                if logger is not None: logger.error(
                    f"BLAST row {line_number} contains {len(row)} columns, expected {len(BLAST_COLUMNS)}."
                )
                raise ValueError(
                    f"BLAST row {line_number} contains {len(row)} columns, expected {len(BLAST_COLUMNS)}."
                )
            match = dict(zip(BLAST_COLUMNS, row, strict = True))
            try:
                for column in INTEGER_COLUMNS:
                    match[column] = int(match[column])
                for column in FLOAT_COLUMNS:
                    match[column] = float(match[column])
            except ValueError as error:
                if logger is not None: logger.error(f"Error parsing BLAST row {line_number}: {error}")
                raise ValueError(f"Error parsing BLAST row {line_number}: {error}") from error
            matches.append(match)
    
    if logger is not None: logger.info(f"Parsed {len(matches)} BLAST matches from {blast_path}.")
    return matches

def rank_blast_matches(matches: list[dict]) -> list[dict]:
    """Rank BLAST matches based on pident and length.
    
    Args:
        matches (list[dict]): List of BLAST matches.
    
    Returns:
        list[dict]: Ranked list of BLAST matches.
    """
    # Initializing empty best_by_subject dictionary.
    best_by_subject = {}

    # Iterating through matches - running a max algorithm to determine best match per subject.
    for match in matches:
        subject_id = match["sseqid"]
        current_best = best_by_subject.get(subject_id)

        # Checking if current match is better than current best.
        if current_best is None:
            best_by_subject[subject_id] = match
            continue

        if _ranking_key(match) < _ranking_key(current_best):
            best_by_subject[subject_id] = match
    
    ranked_matches = sorted(
        best_by_subject.values(),
        key = _ranking_key,
    )

    return ranked_matches

def select_top_blast_matches(matches: list[dict], maximum_matches: int = 6, logger: Logger | None = None) -> list[dict]:
    """Select the highest-ranked unique BLAST matches.
    
    Args:
        matches (list[dict]): List of BLAST matches.
        maximum_matches (int, optional): Maximum number of matches to select. Defaults to 6.
    
    Returns:
        list[dict]: Ranked list of BLAST matches.
    """
    # Verifying that maximum matches is greater than 0.
    if maximum_matches <= 0:
        if logger is not None: logger.error("Maximum matches must be greater than 0.")
        raise ValueError("Maximum matches must be greater than 0.")
    
    # Initializing empty selected matches list.
    selected_matches = []

    # Ranking matches.
    ranked_matches = rank_blast_matches(matches)
    
    # Selecting top matches.
    for rank, match in enumerate(ranked_matches[:maximum_matches], start = 1):
        selected_match = dict(match)
        selected_match["rank"] = rank
        selected_matches.append(selected_match)

    # Returning selected matches.
    return selected_matches

def write_top_blast_matches(
        matches: list[dict],
        output_path: str | Path,
        sample_id: str,
        logger: Logger | None = None,
) -> None:
    """Write selected BLAST matches to a TSV file.
    
    Args:
        matches (list[dict]): List of BLAST matches.
        output_path (str | Path): Path to output file.
        sample_id (str): Sample ID.
        logger (Logger | None, optional): Logger to use. Defaults to None.
    """
    # Normalizing output path.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents = True, exist_ok = True)

    # Initializing output columns.
    output_columns = [
        "sample_id",
        "rank",
        *BLAST_COLUMNS, 
    ]

    # Writing blast tsv.
    with output_path.open("w", encoding = "utf-8", newline = "",) as handle:
        writer = csv.DictWriter(handle, fieldnames = output_columns, delimiter = "\t", extrasaction = "ignore")
        writer.writeheader()
        for match in matches: 
            row = {"sample_id": sample_id, **match,}
            writer.writerow(row)
    
    # Logging.
    if logger is not None: logger.info(f"Wrote {len(matches)} BLAST matches to {output_path}.")

def _ranking_key(match: dict) -> tuple:
    """Return deterministic BLAST ranking key.
    
    Lower tuple values represent better matches.

    Args: 
        match (dict): BLAST match.

    Returns:
        tuple: BLAST ranking key.
    """
    return (
        match["evalue"],
        -match["bitscore"],
        -match["qcovs"],
        -match["pident"],
        -match["length"],
        match["sseqid"]
    )