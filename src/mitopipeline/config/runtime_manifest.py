"""runtime_manifest.py

Create a normalized runtime sample manifest from either a user-provided
manifest or a directory containing paired-end FASTQ files.
"""

# Imports
import logging
import re
from pathlib import Path
from typing import Iterable

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

PAIR_PATTERNS = (
    re.compile(
        r"^(?P<sample>.+?)(?:_R)(?P<read>[12])"
        r"(?:_\d+)?\.(?:fastq|fq)(?:\.gz)?$",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<sample>.+?)[._-](?P<read>[12])"
        r"\.(?:fastq|fq)(?:\.gz)?$",
        flags=re.IGNORECASE,
    ),
)


def is_fastq_path(
        path: str | Path,
) -> bool:
    """Return whether a path has a supported FASTQ suffix.

    Args:
        path (str | Path): Path to inspect.

    Returns:
        bool: True when the path looks like a FASTQ file.
    """
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
        sample_1.fq.gz
        sample_2.fq.gz

    Args:
        path (str | Path): FASTQ path.

    Returns:
        tuple[str, int] | None: Sample ID and read number, or None when
            the filename does not match a supported pairing convention.
    """
    filename = Path(path).name

    for pattern in PAIR_PATTERNS:
        match = pattern.match(filename)

        if match is None:
            continue

        sample_id = match.group("sample").strip(
            "._-"
        )

        read_number = int(
            match.group("read")
        )

        if not sample_id:
            return None

        return sample_id, read_number

    return None


def normalize_sample_id(
        sample_id: object,
) -> str:
    """Normalize and validate a sample identifier.

    Args:
        sample_id (object): Sample identifier value.

    Returns:
        str: Normalized sample ID.

    Raises:
        ValueError: If the sample ID is empty.
    """
    normalized = str(sample_id).strip()

    if not normalized:
        raise ValueError(
            "Sample ID cannot be empty."
        )

    return normalized


def resolve_manifest_path(
        value: object,
        manifest_directory: Path,
) -> Path:
    """Resolve a manifest file path.

    Relative paths are interpreted relative to the source manifest.

    Args:
        value (object): Manifest path value.
        manifest_directory (Path): Source manifest directory.

    Returns:
        Path: Absolute resolved path.

    Raises:
        ValueError: If the path is empty.
    """
    raw_value = str(value).strip()

    if not raw_value:
        raise ValueError(
            "Manifest FASTQ paths cannot be empty."
        )

    path = Path(raw_value).expanduser()

    if not path.is_absolute():
        path = (
            manifest_directory
            / path
        )

    return path.resolve()


def validate_fastq_file(
        path: str | Path,
        column_name: str,
        sample_id: str,
) -> None:
    """Validate a FASTQ file path.

    Args:
        path (str | Path): FASTQ path.
        column_name (str): Manifest column name.
        sample_id (str): Sample identifier.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a supported FASTQ file.
    """
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
    """Validate required runtime-manifest columns.

    Args:
        table (pd.DataFrame): Manifest table.

    Raises:
        ValueError: If required columns are missing.
    """
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


def normalize_manifest_table(
        table: pd.DataFrame,
        manifest_directory: str | Path,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Normalize a manifest DataFrame.

    Args:
        table (pd.DataFrame): Source manifest table.
        manifest_directory (str | Path): Directory used to resolve
            relative FASTQ paths.
        validate_files (bool, optional): Whether FASTQ files must exist.
            Defaults to True.
        logger (logging.Logger | None, optional): Logger. Defaults to
            None.

    Returns:
        pd.DataFrame: Normalized manifest table.

    Raises:
        ValueError: If records are invalid.
    """
    manifest_directory = Path(
        manifest_directory
    ).resolve()

    table = table.copy()

    validate_manifest_columns(
        table
    )

    if table.empty:
        raise ValueError(
            "Manifest contains no samples."
        )

    table["sample_id"] = table[
        "sample_id"
    ].map(
        normalize_sample_id
    )

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
                resolve_manifest_path(
                    value=value,
                    manifest_directory=manifest_directory,
                )
            )
        )

    duplicate_r1 = table["r1"].duplicated(
        keep=False
    )

    if duplicate_r1.any():
        raise ValueError(
            "One or more R1 FASTQ files are assigned to "
            "multiple samples."
        )

    duplicate_r2 = table["r2"].duplicated(
        keep=False
    )

    if duplicate_r2.any():
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

    # Keep the required columns first while preserving optional metadata.
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


def load_source_manifest(
        manifest_path: str | Path,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Load and normalize a user-provided manifest.

    Args:
        manifest_path (str | Path): Source TSV manifest.
        validate_files (bool, optional): Whether FASTQ files must exist.
            Defaults to True.
        logger (logging.Logger | None, optional): Logger. Defaults to
            None.

    Returns:
        pd.DataFrame: Normalized manifest.

    Raises:
        FileNotFoundError: If the manifest does not exist.
    """
    manifest_path = Path(
        manifest_path
    ).expanduser().resolve()

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Source manifest not found: {manifest_path}."
        )

    if not manifest_path.is_file():
        raise ValueError(
            f"Source manifest path is not a file: "
            f"{manifest_path}."
        )

    table = pd.read_csv(
        manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    normalized = normalize_manifest_table(
        table=table,
        manifest_directory=manifest_path.parent,
        validate_files=validate_files,
        logger=logger,
    )

    if logger is not None:
        logger.info(
            f"Loaded source manifest: {manifest_path}."
        )

    return normalized


def discover_fastq_files(
        input_directory: str | Path,
) -> list[Path]:
    """Recursively discover supported FASTQ files.

    Args:
        input_directory (str | Path): Input dataset directory.

    Returns:
        list[Path]: Sorted FASTQ paths.

    Raises:
        FileNotFoundError: If the input directory does not exist.
        ValueError: If the path is not a directory.
    """
    input_directory = Path(
        input_directory
    ).expanduser().resolve()

    if not input_directory.exists():
        raise FileNotFoundError(
            f"Input directory not found: {input_directory}."
        )

    if not input_directory.is_dir():
        raise ValueError(
            f"Input path is not a directory: "
            f"{input_directory}."
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
    """Construct a minimal manifest from paired FASTQ files.

    Args:
        input_directory (str | Path): Dataset root directory.
        logger (logging.Logger | None, optional): Logger. Defaults to
            None.

    Returns:
        pd.DataFrame: Minimal normalized runtime manifest.

    Raises:
        ValueError: If files cannot be paired unambiguously.
    """
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
                    "r1": str(
                        r1_candidates[0]
                    ),
                    "r2": str(
                        r2_candidates[0]
                    ),
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

    normalized = normalize_manifest_table(
        table=table,
        manifest_directory=Path(
            input_directory
        ),
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
    """Write a normalized runtime manifest.

    Args:
        table (pd.DataFrame): Normalized manifest table.
        output_path (str | Path): Runtime manifest output path.
        logger (logging.Logger | None, optional): Logger. Defaults to
            None.

    Returns:
        Path: Absolute runtime-manifest path.
    """
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
        source_manifest: str | Path | None = None,
        input_directory: str | Path | None = None,
        validate_files: bool = True,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Create the runtime manifest used by the workflow.

    A source manifest takes precedence when both input sources are given.

    Args:
        output_path (str | Path): Runtime manifest destination.
        source_manifest (str | Path | None, optional): User manifest.
        input_directory (str | Path | None, optional): FASTQ dataset
            directory.
        validate_files (bool, optional): Whether input files must exist.
            Defaults to True.
        logger (logging.Logger | None, optional): Logger. Defaults to
            None.

    Returns:
        pd.DataFrame: Runtime manifest indexed by sample ID.

    Raises:
        ValueError: If neither input source is configured.
    """
    has_manifest = (
        source_manifest is not None
        and str(source_manifest).strip()
    )

    has_input_directory = (
        input_directory is not None
        and str(input_directory).strip()
    )

    if has_manifest:
        table = load_source_manifest(
            manifest_path=source_manifest,
            validate_files=validate_files,
            logger=logger,
        )

        source_type = "source manifest"

    elif has_input_directory:
        table = construct_manifest_from_directory(
            input_directory=input_directory,
            logger=logger,
        )

        source_type = "FASTQ directory discovery"

    else:
        raise ValueError(
            "Either 'manifest' or 'input_directory' must be "
            "configured."
        )

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