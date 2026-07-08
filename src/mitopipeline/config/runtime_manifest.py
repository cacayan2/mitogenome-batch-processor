"""runtime_manifest.py

Create a normalized runtime sample manifest from either a user-provided
manifest or a directory containing paired-end FASTQ files.

The input directory is always required. When a source manifest is supplied,
FASTQ entries are interpreted as filenames located inside the input directory.
When no source manifest is supplied, FASTQ files are discovered directly from
the input directory.
"""

# Imports
import logging
import re
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = (
    "sample_id",
    "r1",
    "r2",
)

FASTQ_SUFFIXES = (
    ".fastq",
    ".fastq.gz",
    ".fq",
    ".fq.gz",
)

MANIFEST_COLUMN_ALIASES = {
    "run": "run",
    "sample_number": "sample_number",
    "sample_no": "sample_number",
    "sample_num": "sample_number",
    "genus": "genus",
    "species": "species",
    "subspecies": "subspecies",
    "museum": "museum",
    "mus_id": "mus_id",
    "museum_id": "mus_id",
    "tube_id": "tube_id",
    "conc_ng_ul": "conc_ng_ul",
    "concentration": "conc_ng_ul",
    "fastq_name_r1_r2": "fastq_filename",
    "fastq_filename": "fastq_filename",
    "filename": "fastq_filename",
    "file_name": "fastq_filename",
    "sample_id": "sample_id",
    "r1": "r1",
    "r2": "r2",
}

DISCARDED_MANIFEST_COLUMNS = {
    "sample_number",
    "dups",
    "gc",
    "median_len",
    "seqs",
}

PAIR_PATTERNS = (
    re.compile(
        r"^(?P<sample>.+?)_R(?P<read>[12])"
        r"(?:_\d+)?(?:\.(?:fastq|fq)(?:\.gz)?)?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<sample>.+?)[._-](?P<read>[12])"
        r"(?:\.(?:fastq|fq)(?:\.gz)?)?$",
        flags=re.IGNORECASE,
    ),
)


def is_fastq_path(path: str | Path) -> bool:
    """Return whether a path has a supported FASTQ suffix."""
    name = Path(path).name.lower()

    return any(
        name.endswith(suffix)
        for suffix in FASTQ_SUFFIXES
    )


def parse_fastq_filename(
        path: str | Path,
) -> tuple[str, int] | None:
    """Parse a sample ID and read number from a FASTQ filename.

    Supported examples include:

        sample_R1.fastq.gz
        sample_R2.fastq.gz
        sample_R1_001.fastq.gz
        sample_R2_001.fastq.gz
        sample_R1_001
        sample_R2_001
        sample_1.fq.gz
        sample_2.fq.gz
    """
    filename = Path(path).name

    for pattern in PAIR_PATTERNS:
        match = pattern.match(filename)

        if match is None:
            continue

        sample_id = match.group("sample").strip("._-")
        read_number = int(match.group("read"))

        if not sample_id:
            return None

        return sample_id, read_number

    return None


def normalize_sample_id(sample_id: object) -> str:
    """Normalize and validate a sample identifier."""
    normalized = str(sample_id).strip()

    if not normalized:
        raise ValueError(
            "Sample ID cannot be empty."
        )

    return normalized


def normalize_metadata_value(value: object) -> str:
    """Normalize an optional source-manifest metadata value."""
    normalized = str(value).strip()

    if normalized.lower() in {
        "",
        "nan",
        "none",
        "null",
    }:
        return ""

    return normalized


def normalize_column_name(column_name: object) -> str:
    """Normalize a source-manifest column name."""
    normalized = str(column_name).strip().lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    ).strip("_")

    return MANIFEST_COLUMN_ALIASES.get(
        normalized,
        normalized,
    )


def normalize_source_columns(
        table: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize source-manifest columns and remove ignored QC fields."""
    table = table.copy()

    normalized_columns = [
        normalize_column_name(column)
        for column in table.columns
    ]

    duplicate_columns = sorted(
        {
            column
            for column in normalized_columns
            if normalized_columns.count(column) > 1
        }
    )

    if duplicate_columns:
        raise ValueError(
            "Source manifest contains columns that normalize "
            "to duplicate names: "
            + ", ".join(duplicate_columns)
            + "."
        )

    table.columns = normalized_columns

    columns_to_drop = [
        column
        for column in table.columns
        if column in DISCARDED_MANIFEST_COLUMNS
    ]

    return table.drop(
        columns=columns_to_drop,
        errors="ignore",
    )


def validate_input_directory(
        input_directory: str | Path | None,
) -> Path:
    """Validate and resolve the required FASTQ input directory."""
    if input_directory is None or not str(input_directory).strip():
        raise ValueError(
            "'input_directory' is required."
        )

    resolved = Path(
        input_directory
    ).expanduser().resolve()

    if not resolved.exists():
        raise FileNotFoundError(
            f"Input directory not found: {resolved}."
        )

    if not resolved.is_dir():
        raise ValueError(
            f"Input path is not a directory: {resolved}."
        )

    return resolved


def validate_fastq_file(
        path: str | Path,
        column_name: str,
        sample_id: str,
) -> None:
    """Validate a resolved FASTQ file."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"{column_name} FASTQ for sample {sample_id} "
            f"does not exist: {path}."
        )

    if not path.is_file():
        raise ValueError(
            f"{column_name} path for sample {sample_id} "
            f"is not a file: {path}."
        )

    if not is_fastq_path(path):
        raise ValueError(
            f"{column_name} path for sample {sample_id} "
            f"is not a supported FASTQ file: {path}."
        )


def validate_manifest_columns(
        table: pd.DataFrame,
) -> None:
    """Validate required runtime-manifest columns."""
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in table.columns
    ]

    if missing_columns:
        raise ValueError(
            "Manifest is missing required columns: "
            + ", ".join(missing_columns)
            + "."
        )


def supported_fastq_names(
        supplied_name: str,
) -> list[str]:
    """Return candidate FASTQ filenames for a manifest value."""
    supplied_name = supplied_name.strip()

    if not supplied_name:
        raise ValueError(
            "FASTQ filename cannot be empty."
        )

    if is_fastq_path(supplied_name):
        return [
            supplied_name,
        ]

    return [
        supplied_name + suffix
        for suffix in FASTQ_SUFFIXES
    ]


def resolve_input_filename(
        filename: object,
        input_directory: str | Path,
        require_exists: bool = True,
) -> Path:
    """Resolve a filename against the configured input directory.

    Source manifests must contain filenames only. Directory components and
    absolute paths are rejected.
    """
    raw_filename = str(filename).strip()

    if not raw_filename:
        raise ValueError(
            "Manifest FASTQ filename cannot be empty."
        )

    supplied_path = Path(raw_filename)

    if supplied_path.is_absolute():
        raise ValueError(
            "Source manifests must contain FASTQ filenames, "
            f"not absolute paths: {raw_filename}."
        )

    if supplied_path.parent != Path("."):
        raise ValueError(
            "Source manifests must contain FASTQ filenames only, "
            f"not relative paths: {raw_filename}."
        )

    input_directory = Path(input_directory).expanduser().resolve()

    candidates = [
        input_directory / candidate_name
        for candidate_name in supported_fastq_names(
            raw_filename
        )
    ]

    matching_paths = [
        candidate.resolve()
        for candidate in candidates
        if candidate.exists()
        and candidate.is_file()
    ]

    if len(matching_paths) == 1:
        return matching_paths[0]

    if len(matching_paths) > 1:
        raise ValueError(
            f"FASTQ filename {raw_filename} matched multiple files: "
            + ", ".join(
                str(path)
                for path in matching_paths
            )
            + "."
        )

    if not require_exists:
        return candidates[0].resolve()

    raise FileNotFoundError(
        f"FASTQ file {raw_filename} was not found under "
        f"{input_directory}. Tried: "
        + ", ".join(
            path.name
            for path in candidates
        )
        + "."
    )


def read_source_manifest(
        manifest_path: str | Path,
) -> pd.DataFrame:
    """Read an Excel, TSV, TXT, or CSV source manifest."""
    manifest_path = Path(manifest_path)
    suffix = manifest_path.suffix.lower()

    if suffix in {
        ".xlsx",
        ".xlsm",
    }:
        return pd.read_excel(
            manifest_path,
            dtype=str,
            keep_default_na=False,
        )

    if suffix in {
        ".tsv",
        ".txt",
    }:
        return pd.read_csv(
            manifest_path,
            sep="\t",
            dtype=str,
            keep_default_na=False,
        )

    if suffix == ".csv":
        return pd.read_csv(
            manifest_path,
            dtype=str,
            keep_default_na=False,
        )

    raise ValueError(
        "Unsupported manifest format. Expected one of: "
        ".xlsx, .xlsm, .tsv, .txt, or .csv."
    )


def normalize_runtime_table(
        table: pd.DataFrame,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Validate and normalize a one-row-per-sample runtime table."""
    table = table.copy()

    validate_manifest_columns(table)

    if table.empty:
        raise ValueError(
            "Manifest contains no samples."
        )

    table["sample_id"] = table[
        "sample_id"
    ].map(normalize_sample_id)

    if table["sample_id"].duplicated().any():
        duplicates = sorted(
            table.loc[
                table["sample_id"].duplicated(
                    keep=False
                ),
                "sample_id",
            ].unique()
        )

        raise ValueError(
            "Duplicate sample IDs found in manifest: "
            + ", ".join(duplicates)
            + "."
        )

    for column_name in (
        "r1",
        "r2",
    ):
        table[column_name] = table[
            column_name
        ].map(
            lambda value: str(
                Path(value).expanduser().resolve()
            )
        )

    if table["r1"].duplicated(
            keep=False
    ).any():
        raise ValueError(
            "One or more R1 FASTQ files are assigned to "
            "multiple samples."
        )

    if table["r2"].duplicated(
            keep=False
    ).any():
        raise ValueError(
            "One or more R2 FASTQ files are assigned to "
            "multiple samples."
        )

    same_mate = table["r1"] == table["r2"]

    if same_mate.any():
        invalid_samples = table.loc[
            same_mate,
            "sample_id",
        ].tolist()

        raise ValueError(
            "R1 and R2 point to the same file for samples: "
            + ", ".join(invalid_samples)
            + "."
        )

    if validate_files:
        for row in table.itertuples(
            index=False
        ):
            validate_fastq_file(
                path=row.r1,
                column_name="R1",
                sample_id=row.sample_id,
            )

            validate_fastq_file(
                path=row.r2,
                column_name="R2",
                sample_id=row.sample_id,
            )

    optional_columns = [
        column
        for column in table.columns
        if column not in REQUIRED_COLUMNS
    ]

    table = table[
        list(REQUIRED_COLUMNS)
        + optional_columns
    ]

    table = table.sort_values(
        by="sample_id",
        kind="stable",
    ).reset_index(
        drop=True
    )

    if logger is not None:
        logger.info(
            f"Normalized manifest containing "
            f"{len(table)} samples."
        )

    return table


def parse_manifest_fastq_name(
        filename: object,
) -> tuple[str, int]:
    """Extract a sample ID and read number from a manifest filename."""
    raw_filename = str(filename).strip()
    parsed = parse_fastq_filename(raw_filename)

    if parsed is None:
        raise ValueError(
            "Could not determine R1/R2 pairing from manifest "
            f"filename: {raw_filename}."
        )

    return parsed


def combine_pair_metadata(
        sample_id: str,
        rows: pd.DataFrame,
        metadata_columns: list[str],
) -> dict[str, str]:
    """Combine metadata shared by an R1/R2 pair."""
    metadata: dict[str, str] = {}

    for column in metadata_columns:
        values = {
            normalize_metadata_value(value)
            for value in rows[column].tolist()
        }

        values.discard("")

        if len(values) > 1:
            raise ValueError(
                f"Conflicting {column} values for paired sample "
                f"{sample_id}: {sorted(values)}."
            )

        metadata[column] = (
            next(iter(values))
            if values
            else ""
        )

    return metadata


def convert_row_per_sample_manifest(
        table: pd.DataFrame,
        input_directory: str | Path,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Normalize a conventional one-row-per-sample manifest."""
    required_source_columns = {
        "sample_id",
        "r1",
        "r2",
    }

    missing_columns = (
        required_source_columns
        - set(table.columns)
    )

    if missing_columns:
        raise ValueError(
            "One-row-per-sample manifest is missing columns: "
            + ", ".join(
                sorted(missing_columns)
            )
            + "."
        )

    table = table.copy()

    table["r1"] = table[
        "r1"
    ].map(
        lambda filename: str(
            resolve_input_filename(
                filename=filename,
                input_directory=input_directory,
                require_exists=validate_files,
            )
        )
    )

    table["r2"] = table[
        "r2"
    ].map(
        lambda filename: str(
            resolve_input_filename(
                filename=filename,
                input_directory=input_directory,
                require_exists=validate_files,
            )
        )
    )

    return normalize_runtime_table(
        table=table,
        validate_files=validate_files,
        logger=logger,
    )


def convert_row_per_read_manifest(
        table: pd.DataFrame,
        input_directory: str | Path,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Convert a one-row-per-read manifest into one row per sample."""
    if "fastq_filename" not in table.columns:
        raise ValueError(
            "Row-per-read manifest must contain a FASTQ filename "
            "column such as 'Fastq_name_R1_R2'."
        )

    table = table.copy()

    parsed_values = table[
        "fastq_filename"
    ].map(parse_manifest_fastq_name)

    table["sample_id"] = [
        sample_id
        for sample_id, _ in parsed_values
    ]

    table["read_number"] = [
        read_number
        for _, read_number in parsed_values
    ]

    metadata_columns = [
        column
        for column in table.columns
        if column not in {
            "sample_id",
            "read_number",
            "fastq_filename",
            "r1",
            "r2",
        }
    ]

    records: list[dict[str, str]] = []

    for sample_id, sample_rows in table.groupby(
            "sample_id",
            sort=True,
    ):
        r1_rows = sample_rows.loc[
            sample_rows["read_number"] == 1
        ]

        r2_rows = sample_rows.loc[
            sample_rows["read_number"] == 2
        ]

        if len(r1_rows) != 1:
            raise ValueError(
                f"Sample {sample_id} must contain exactly one R1 "
                f"row; found {len(r1_rows)}."
            )

        if len(r2_rows) != 1:
            raise ValueError(
                f"Sample {sample_id} must contain exactly one R2 "
                f"row; found {len(r2_rows)}."
            )

        r1_name = r1_rows.iloc[0][
            "fastq_filename"
        ]

        r2_name = r2_rows.iloc[0][
            "fastq_filename"
        ]

        r1_path = resolve_input_filename(
            filename=r1_name,
            input_directory=input_directory,
            require_exists=validate_files,
        )

        r2_path = resolve_input_filename(
            filename=r2_name,
            input_directory=input_directory,
            require_exists=validate_files,
        )

        metadata = combine_pair_metadata(
            sample_id=sample_id,
            rows=sample_rows,
            metadata_columns=metadata_columns,
        )

        records.append(
            {
                "sample_id": sample_id,
                "r1": str(r1_path),
                "r2": str(r2_path),
                **metadata,
            }
        )

    normalized = pd.DataFrame.from_records(
        records
    )

    return normalize_runtime_table(
        table=normalized,
        validate_files=validate_files,
        logger=logger,
    )


def load_source_manifest(
        manifest_path: str | Path,
        input_directory: str | Path,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Load and normalize a user-provided source manifest.

    Supported layouts:

    1. One row per sample with sample_id, r1, and r2.
    2. One row per read with Fastq_name_R1_R2 or an accepted alias.
    """
    manifest_path = Path(
        manifest_path
    ).expanduser().resolve()

    input_directory = validate_input_directory(
        input_directory
    )

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Source manifest not found: {manifest_path}."
        )

    if not manifest_path.is_file():
        raise ValueError(
            f"Source manifest path is not a file: "
            f"{manifest_path}."
        )

    table = read_source_manifest(
        manifest_path
    )

    table = normalize_source_columns(
        table
    )

    if {
        "sample_id",
        "r1",
        "r2",
    }.issubset(
        table.columns
    ):
        normalized = convert_row_per_sample_manifest(
            table=table,
            input_directory=input_directory,
            validate_files=validate_files,
            logger=logger,
        )

    elif "fastq_filename" in table.columns:
        normalized = convert_row_per_read_manifest(
            table=table,
            input_directory=input_directory,
            validate_files=validate_files,
            logger=logger,
        )

    else:
        raise ValueError(
            "Source manifest must contain either "
            "'sample_id', 'r1', and 'r2', or a filename column "
            "such as 'Fastq_name_R1_R2'."
        )

    if logger is not None:
        logger.info(
            f"Loaded source manifest: {manifest_path}."
        )

    return normalized


def discover_fastq_files(
        input_directory: str | Path,
) -> list[Path]:
    """Recursively discover supported FASTQ files."""
    input_directory = validate_input_directory(
        input_directory
    )

    return sorted(
        path.resolve()
        for path in input_directory.rglob("*")
        if path.is_file()
        and is_fastq_path(path)
    )


def construct_manifest_from_directory(
        input_directory: str | Path,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Construct a minimal runtime manifest from paired FASTQ files."""
    fastq_paths = discover_fastq_files(
        input_directory
    )

    if not fastq_paths:
        raise ValueError(
            f"No FASTQ files were found under "
            f"{Path(input_directory).resolve()}."
        )

    pairs: dict[
        str,
        dict[int, list[Path]],
    ] = {}

    ignored_files: list[Path] = []

    for fastq_path in fastq_paths:
        parsed = parse_fastq_filename(
            fastq_path
        )

        if parsed is None:
            ignored_files.append(
                fastq_path
            )
            continue

        sample_id, read_number = parsed

        pairs.setdefault(
            sample_id,
            {
                1: [],
                2: [],
            },
        )[read_number].append(
            fastq_path
        )

    if not pairs:
        raise ValueError(
            "FASTQ files were found, but none matched a supported "
            "paired-end naming convention."
        )

    records: list[dict[str, str]] = []
    errors: list[str] = []

    for sample_id in sorted(pairs):
        sample_pairs = pairs[
            sample_id
        ]

        r1_candidates = sample_pairs[1]
        r2_candidates = sample_pairs[2]

        if len(r1_candidates) != 1:
            errors.append(
                f"{sample_id}: expected exactly one R1 file, "
                f"found {len(r1_candidates)}"
            )

        if len(r2_candidates) != 1:
            errors.append(
                f"{sample_id}: expected exactly one R2 file, "
                f"found {len(r2_candidates)}"
            )

        if (
            len(r1_candidates) == 1
            and len(r2_candidates) == 1
        ):
            records.append(
                {
                    "sample_id": sample_id,
                    "r1": str(r1_candidates[0]),
                    "r2": str(r2_candidates[0]),
                }
            )

    if errors:
        raise ValueError(
            "Could not construct unambiguous FASTQ pairs:\n- "
            + "\n- ".join(errors)
        )

    table = pd.DataFrame.from_records(
        records,
        columns=REQUIRED_COLUMNS,
    )

    normalized = normalize_runtime_table(
        table=table,
        validate_files=True,
        logger=logger,
    )

    if logger is not None:
        logger.info(
            f"Constructed manifest from "
            f"{len(fastq_paths)} FASTQ files."
        )

        if ignored_files:
            logger.warning(
                f"Ignored {len(ignored_files)} FASTQ files whose "
                "names did not match supported pairing conventions."
            )

    return normalized


def write_runtime_manifest(
        table: pd.DataFrame,
        output_path: str | Path,
        logger: logging.Logger | None = None,
) -> Path:
    """Write a normalized runtime manifest atomically."""
    output_path = Path(
        output_path
    ).expanduser().resolve()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    table.to_csv(
        temporary_path,
        sep="\t",
        index=False,
        lineterminator="\n",
    )

    temporary_path.replace(
        output_path
    )

    if logger is not None:
        logger.info(
            f"Wrote runtime manifest to {output_path}."
        )

    return output_path


def prepare_runtime_manifest(
        output_path: str | Path,
        input_directory: str | Path | None,
        source_manifest: str | Path | None = None,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Create the authoritative runtime manifest used by Snakemake."""
    input_directory = validate_input_directory(
        input_directory
    )

    has_manifest = (
        source_manifest is not None
        and bool(str(source_manifest).strip())
    )

    if has_manifest:
        table = load_source_manifest(
            manifest_path=source_manifest,
            input_directory=input_directory,
            validate_files=validate_files,
            logger=logger,
        )

        source_type = "source manifest"

    else:
        table = construct_manifest_from_directory(
            input_directory=input_directory,
            logger=logger,
        )

        source_type = "FASTQ directory discovery"

    runtime_path = write_runtime_manifest(
        table=table,
        output_path=output_path,
        logger=logger,
    )

    if logger is not None:
        logger.info(
            f"Prepared runtime manifest from {source_type}: "
            f"{runtime_path}."
        )

    return table.set_index(
        "sample_id",
        drop=True,
    )
