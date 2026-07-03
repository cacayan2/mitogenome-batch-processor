"""mitos2_stats.py

Parser for extracting annotation statistics from MITOS2 outputs."""

# Imports
from pathlib import Path
import logging

from mitopipeline.models.annotation_stats import AnnotationStats

PROTEIN_CODING_GENES = {
    "atp6",
    "atp8",
    "atp9",
    "cob",
    "cox1",
    "cox2",
    "cox3",
    "nad1",
    "nad2",
    "nad3",
    "nad4",
    "nad4l",
    "nad5",
    "nad6",
}

def parse_gff_attributes(attribute_string: str) -> dict[str, str]:
    """Parse the attributes column from a GFF row.
    
    Args: 
        attribute_string (str): The attributes column from a GFF row.
    
    Returns:
        dict[str, str]: A dictionary of attributes.
    """
    # Initialize attributes.
    attributes = {}

    # Parsing key-value pairs.
    for item in attribute_string.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        attributes[key.strip()] = value.strip()

    # Returning parsed attributes.
    return attributes

def parse_mitos2_gff(
        gff_path: Path,
        logger: logging.Logger | None = None
) -> list[dict[str, str]]:
    """Parse MITOS2 GFF rows.
    
    Args:
        gff_path (Path): The path to the GFF file.
        logger (Logger | None, optional): The logger to use. Defaults to None.

    Returns:
        list[dict[str, str]]: A list of dictionaries representing the parsed GFF rows.
    """
    # Validating inputs.
    if not gff_path.exists():
        if logger is not None: logger.error(f"GFF file {gff_path} does not exist.")
        raise FileNotFoundError(f"GFF file {gff_path} does not exist.")
    if not gff_path.is_file():
        if logger is not None: logger.error(f"GFF file {gff_path} is not a file.")
        raise ValueError(f"GFF file {gff_path} is not a file.")
    
    # Logging.
    if logger is not None: logger.info(f"Parsing MITOS2 GFF file: {gff_path}")

    # Initializing features.
    features = []

    # Reading GFF.
    with gff_path.open("r", encoding = "utf-8") as handle:
        for line in handle:
            line = line.strip()

            # Skipping blank/comment lines.
            if not line or line.startswith("#"):
                continue

            # Splitting GFF columns.
            parts = line.split("\t")

            if len(parts) != 9:
                if logger is not None: logger.error(f"Malformed GFF row in {gff_path}: {line}")
                raise ValueError(f"Malformed GFF row in {gff_path}: {line}")
            
            attributes = parse_gff_attributes(parts[8])

            features.append(
                {
                    "seqid": parts[0],
                    "source": parts[1],
                    "type": parts[2],
                    "start": parts[3],
                    "end": parts[4],
                    "score": parts[5],
                    "strand": parts[6],
                    "phase": parts[7],
                    "attributes": attributes,
                    "name": attributes.get("Name", ""),
                    "gene_id": attributes.get("gene_id", ""),
                }
            )

    # Logging.
    if logger is not None: logger.info(f"Parsed {len(features)} MITOS2 GFF features from {gff_path}.")

    # Returning features
    return features

def parse_mitos2_warnings(
        mitos_path: Path | None, 
        logger: logging.Logger | None = None
) -> list[str]:
    """Parse MITOS2 warnings if a stable warning source exists.

    Args:
        mitos_path (Path | None): The path to the MITOS2 output directory.
        logger (Logger | None, optional): The logger to use. Defaults to None.
    
    Returns:
        list[str]: A list of warnings.
    """
    # Returning empty warnings if no file was provided.
    if mitos_path is None or not mitos_path.exists():
        return []
    
    # Initializing warnings.
    warnings = []

    # Searching warning-like lines.
    with mitos_path.open("r", encoding = "utf-8", errors = "replace") as handle:
        for line in handle:
            stripped = line.strip()

            if "warning" in stripped.lower() or "duplicated" in stripped.lower():
                warnings.append(stripped)

    # Logging.
    if logger is not None: logger.info(f"Found {len(warnings)} MITOS2 warnings.")

    # Returning warnings.
    return warnings

def parse_annotation_stats(
        sample_id: str,
        gff_path: Path,
        mitos_path: Path | None = None,
        logger: logging.Logger | None = None
) -> AnnotationStats:
    """Parses annotation stats from a GFF file and a MITOS2 output directory.

    Args:
        sample_id (str): The sample ID.
        gff_path (Path): The path to the GFF file.
        mitos_path (Path | None, optional): The path to the MITOS2 output directory. Defaults to None.
        logger (Logger | None, optional): The logger to use. Defaults to None.

    Returns:
        AnnotationStats: The parsed annotation stats.
    """

    # Logging.
    if logger is not None: logger.info(f"Parsing MITOS2 annotation stats for sample {sample_id}.")

    # Parsing features.
    features = parse_mitos2_gff(gff_path, logger)

    # Counting feature rows.
    feature_count = len(features)

    # Counting RNA features.
    trna_count = sum(1 for feature in features if feature["type"] == "tRNA")
    rrna_count = sum(1 for feature in features if feature["type"] == "rRNA")

    # Counting gene-like rows.
    gene_count = sum(
        1 for feature in features
        if feature["type"] in {"gene", "ncRNA_gene"}
    )

    # Counting protein-coding genes.
    cds_count = sum(
        1
        for feature in features
        if feature["type"] == "gene"
        and feature["source"] == "mitos"
        and feature["gene_id"].lower() in PROTEIN_CODING_GENES
    )

    # Parsing warnings.
    warnings = parse_mitos2_warnings(mitos_path, logger)

    # Returning stats model.
    return AnnotationStats(
        sample_id = sample_id,
        cds_count = cds_count,
        trna_count = trna_count,
        rrna_count = rrna_count,
        gene_count = gene_count,
        feature_count = feature_count,
        warnings = warnings,
    )