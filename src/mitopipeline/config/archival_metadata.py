"""archival_metadata.py

Schema and validation utilities for NCBI archival metadata preparation.
"""

# Imports
from dataclasses import dataclass
from pathlib import Path
import logging

import pandas as pd


ALLOWED_MISSING_VALUES = {
    "missing",
    "not collected",
    "not applicable",
    "restricted access",
}

REQUIRED_ARCHIVAL_COLUMNS = [
    "sample_id",
    "organism",
    "sample_title",
    "bioproject_title",
    "bioproject_description",
    "biosample_package",
    "isolate",
    "collection_date",
    "geo_loc_name",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "platform",
    "instrument_model",
    "read_1_filename",
    "assembly_fasta_filename",
    "assembly_method",
    "annotation_method",
    "molecule_type",
    "genome_location",
]

OPTIONAL_ARCHIVAL_COLUMNS = [
    "taxonomy_id",
    "subspecies",
    "specimen_voucher",
    "museum",
    "mus_id",
    "tube_id",
    "tissue",
    "sex",
    "life_stage",
    "collected_by",
    "identified_by",
    "lat_lon",
    "host",
    "environmental_sample",
    "sample_description",
    "bioproject_accession",
    "biosample_accession",
    "read_2_filename",
    "library_name",
    "library_construction_protocol",
    "insert_size",
    "sra_experiment_title",
    "sra_experiment_description",
    "sra_accession",
    "coverage",
    "sequence_length_bp",
    "circular",
    "genbank_accession",
    "release_date",
    "submitter_name",
    "submitter_email",
    "organization",
    "notes",
]

ARCHIVAL_COLUMNS = [
    *REQUIRED_ARCHIVAL_COLUMNS,
    *OPTIONAL_ARCHIVAL_COLUMNS,
]

BOOLEAN_COLUMNS = {
    "environmental_sample",
    "circular",
}

VALID_BOOLEAN_VALUES = {
    "true",
    "false",
    *ALLOWED_MISSING_VALUES,
}

VALID_LIBRARY_LAYOUTS = {
    "paired",
    "single",
}


@dataclass(frozen=True)
class ArchivalValidationResult:
    """Validation result for an archival metadata table."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int


def normalize_archival_value(
        value: object,
) -> str:
    """Normalize one archival metadata value."""
    normalized = str(
        value
    ).strip()

    if normalized.lower() in {
        "",
        "nan",
        "none",
        "null",
    }:
        return ""

    return normalized


def read_archival_metadata(
        archival_metadata_path: str | Path,
) -> pd.DataFrame:
    """Read archival metadata from TSV.

    Args:
        archival_metadata_path (str | Path): Metadata TSV path.

    Returns:
        pd.DataFrame: Metadata table.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a TSV file.
    """
    archival_metadata_path = Path(
        archival_metadata_path
    ).expanduser().resolve()

    if not archival_metadata_path.exists():
        raise FileNotFoundError(
            f"Archival metadata file not found: "
            f"{archival_metadata_path}."
        )

    if not archival_metadata_path.is_file():
        raise ValueError(
            f"Archival metadata path is not a file: "
            f"{archival_metadata_path}."
        )

    if archival_metadata_path.suffix.lower() not in {
        ".tsv",
        ".txt",
    }:
        raise ValueError(
            "Archival metadata must be a TSV or TXT file."
        )

    return pd.read_csv(
        archival_metadata_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )


def normalize_archival_metadata_table(
        table: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize archival metadata values and column order."""
    table = table.copy()

    for column in table.columns:
        table[column] = table[
            column
        ].map(
            normalize_archival_value
        )

    known_columns = [
        column
        for column in ARCHIVAL_COLUMNS
        if column in table.columns
    ]

    extra_columns = [
        column
        for column in table.columns
        if column not in ARCHIVAL_COLUMNS
    ]

    return table[
        known_columns
        + extra_columns
    ]


def validate_required_columns(
        table: pd.DataFrame,
) -> list[str]:
    """Validate that all required columns are present."""
    missing_columns = [
        column
        for column in REQUIRED_ARCHIVAL_COLUMNS
        if column not in table.columns
    ]

    if not missing_columns:
        return []

    return [
        "Missing required archival metadata columns: "
        + ", ".join(
            missing_columns
        )
        + "."
    ]


def validate_unique_sample_ids(
        table: pd.DataFrame,
) -> list[str]:
    """Validate sample_id uniqueness."""
    if "sample_id" not in table.columns:
        return []

    duplicate_mask = table[
        "sample_id"
    ].duplicated(
        keep=False
    )

    if not duplicate_mask.any():
        return []

    duplicates = sorted(
        table.loc[
            duplicate_mask,
            "sample_id",
        ].unique()
    )

    return [
        "Duplicate sample_id values found: "
        + ", ".join(
            duplicates
        )
        + "."
    ]


def validate_required_values(
        table: pd.DataFrame,
) -> list[str]:
    """Validate required values are populated."""
    errors: list[str] = []

    for row_index, row in table.iterrows():
        sample_id = row.get(
            "sample_id",
            f"row_{row_index + 1}",
        )

        for column in REQUIRED_ARCHIVAL_COLUMNS:
            if column not in table.columns:
                continue

            value = row[
                column
            ]

            if not value:
                errors.append(
                    f"Sample {sample_id}: required field "
                    f"{column} is empty. Use a real value or "
                    "an allowed missing-value term."
                )

    return errors


def validate_library_layout(
        table: pd.DataFrame,
) -> list[str]:
    """Validate library_layout and paired-end read metadata."""
    errors: list[str] = []

    if "library_layout" not in table.columns:
        return errors

    for row_index, row in table.iterrows():
        sample_id = row.get(
            "sample_id",
            f"row_{row_index + 1}",
        )

        layout = row[
            "library_layout"
        ].lower()

        if layout not in VALID_LIBRARY_LAYOUTS:
            errors.append(
                f"Sample {sample_id}: library_layout must be one "
                f"of {sorted(VALID_LIBRARY_LAYOUTS)}, found "
                f"{row['library_layout']}."
            )

            continue

        if layout == "paired":
            read_2_filename = row.get(
                "read_2_filename",
                "",
            )

            if not read_2_filename:
                errors.append(
                    f"Sample {sample_id}: read_2_filename is "
                    "required when library_layout is paired."
                )

    return errors


def validate_boolean_columns(
        table: pd.DataFrame,
) -> list[str]:
    """Validate boolean-like fields."""
    errors: list[str] = []

    for column in BOOLEAN_COLUMNS:
        if column not in table.columns:
            continue

        for row_index, value in table[
            column
        ].items():
            if not value:
                continue

            if value.lower() not in VALID_BOOLEAN_VALUES:
                sample_id = (
                    table.loc[
                        row_index,
                        "sample_id",
                    ]
                    if "sample_id" in table.columns
                    else f"row_{row_index + 1}"
                )

                errors.append(
                    f"Sample {sample_id}: {column} must be true, "
                    "false, or an allowed missing-value term."
                )

    return errors


def validate_controlled_missing_values(
        table: pd.DataFrame,
) -> list[str]:
    """Warn about informal missing-like values."""
    warnings: list[str] = []

    informal_missing_values = {
        "unknown",
        "n/a",
        "na",
        "none",
        "null",
        "?",
        "-",
    }

    for row_index, row in table.iterrows():
        sample_id = row.get(
            "sample_id",
            f"row_{row_index + 1}",
        )

        for column, value in row.items():
            if value.lower() in informal_missing_values:
                warnings.append(
                    f"Sample {sample_id}: field {column} uses "
                    f"'{value}'. Prefer one of "
                    f"{sorted(ALLOWED_MISSING_VALUES)}."
                )

    return warnings


def validate_archival_metadata_table(
        table: pd.DataFrame,
        logger: logging.Logger | None = None,
) -> ArchivalValidationResult:
    """Validate an archival metadata table."""
    table = normalize_archival_metadata_table(
        table
    )

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(
        validate_required_columns(
            table
        )
    )

    errors.extend(
        validate_unique_sample_ids(
            table
        )
    )

    errors.extend(
        validate_required_values(
            table
        )
    )

    errors.extend(
        validate_library_layout(
            table
        )
    )

    errors.extend(
        validate_boolean_columns(
            table
        )
    )

    warnings.extend(
        validate_controlled_missing_values(
            table
        )
    )

    result = ArchivalValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        row_count=len(
            table
        ),
    )

    if logger is not None:
        logger.info(
            f"Validated archival metadata table with "
            f"{result.row_count} rows."
        )

        for warning in warnings:
            logger.warning(
                warning
            )

        for error in errors:
            logger.error(
                error
            )

    return result


def validate_archival_metadata_file(
        archival_metadata_path: str | Path,
        logger: logging.Logger | None = None,
) -> ArchivalValidationResult:
    """Read and validate an archival metadata TSV file."""
    table = read_archival_metadata(
        archival_metadata_path
    )

    return validate_archival_metadata_table(
        table=table,
        logger=logger,
    )


def write_example_archival_metadata(
        output_path: str | Path,
) -> Path:
    """Write an example archival metadata TSV."""
    output_path = Path(
        output_path
    ).expanduser().resolve()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    example = pd.DataFrame(
        [
            {
                "sample_id": "example_sample_001",
                "organism": "Example species",
                "taxonomy_id": "missing",
                "sample_title": "Example mitochondrial genome sample",
                "bioproject_title": "Example mitochondrial genome project",
                "bioproject_description": (
                    "Example project description for mitochondrial "
                    "genome archival preparation."
                ),
                "biosample_package": "Model organism or animal",
                "isolate": "example_sample_001",
                "collection_date": "not collected",
                "geo_loc_name": "not collected",
                "subspecies": "not applicable",
                "specimen_voucher": "not collected",
                "museum": "not collected",
                "mus_id": "not collected",
                "tube_id": "not collected",
                "tissue": "not collected",
                "sex": "missing",
                "life_stage": "missing",
                "collected_by": "not collected",
                "identified_by": "not collected",
                "lat_lon": "restricted access",
                "host": "not applicable",
                "environmental_sample": "false",
                "sample_description": "Example row.",
                "bioproject_accession": "missing",
                "biosample_accession": "missing",
                "library_strategy": "WGS",
                "library_source": "GENOMIC",
                "library_selection": "RANDOM",
                "library_layout": "paired",
                "platform": "ILLUMINA",
                "instrument_model": "missing",
                "library_name": "example_sample_001",
                "library_construction_protocol": "missing",
                "insert_size": "missing",
                "read_1_filename": "example_sample_001_R1.fastq.gz",
                "read_2_filename": "example_sample_001_R2.fastq.gz",
                "sra_experiment_title": (
                    "Example paired-end genomic sequencing"
                ),
                "sra_experiment_description": (
                    "Example paired-end reads for mitochondrial "
                    "genome assembly."
                ),
                "sra_accession": "missing",
                "assembly_fasta_filename": "example_sample_001.fasta",
                "assembly_method": "GetOrganelle; version missing",
                "annotation_method": "MITOS2; version missing",
                "molecule_type": "genomic DNA",
                "genome_location": "mitochondrion",
                "coverage": "missing",
                "sequence_length_bp": "missing",
                "circular": "missing",
                "genbank_accession": "missing",
                "release_date": "missing",
                "submitter_name": "missing",
                "submitter_email": "missing",
                "organization": "missing",
                "notes": "Example only.",
            }
        ],
        columns=ARCHIVAL_COLUMNS,
    )

    example.to_csv(
        output_path,
        sep="\t",
        index=False,
        lineterminator="\n",
    )

    return output_path
