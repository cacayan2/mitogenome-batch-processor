"""Parse and validate MitoPipeline sample manifests."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from mitopipeline.models.sample import Sample


REQUIRED_COLUMNS = {"sample_id", "r1", "r2"}


def parse_sample_manifest(
    manifest_path: Path,
    logger: logging.Logger | None = None,
) -> list[Sample]:
    """Parse a TSV manifest while retaining every nonblank column."""
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Sample manifest file does not exist: {manifest_path}"
        )

    if manifest_path.stat().st_size == 0:
        raise ValueError(
            f"Sample manifest file is empty: {manifest_path}"
        )

    if logger is not None:
        logger.info(
            "Reading sample manifest: %s",
            manifest_path,
        )

    table = pd.read_csv(
        manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    table.columns = [
        str(column).strip().replace("\r", "")
        for column in table.columns
    ]

    if table.empty:
        raise ValueError(
            f"Sample manifest file is empty: {manifest_path}"
        )

    missing_columns = REQUIRED_COLUMNS - set(table.columns)
    if missing_columns:
        raise ValueError(
            "Sample manifest is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    sample_ids = table["sample_id"].astype(str).str.strip()
    duplicate_ids = sorted(
        sample_ids[sample_ids.duplicated(keep=False)].unique()
    )
    if duplicate_ids:
        raise ValueError(
            "Sample manifest contains duplicate sample_id values: "
            f"{duplicate_ids}"
        )

    samples: list[Sample] = []
    manifest_dir = manifest_path.parent

    for index, row in table.iterrows():
        line_number = index + 2
        metadata = _row_metadata(row)

        sample_id = metadata.get("sample_id", "")
        if not sample_id:
            raise ValueError(
                f"Row {line_number} is missing sample_id."
            )

        r1_value = metadata.get("r1", "")
        r2_value = metadata.get("r2", "")

        if not r1_value:
            raise ValueError(
                f"Row {line_number} is missing r1."
            )

        if not r2_value:
            raise ValueError(
                f"Row {line_number} is missing r2."
            )

        r1_path = _resolve_manifest_path(
            r1_value,
            manifest_dir,
        )
        r2_path = _resolve_manifest_path(
            r2_value,
            manifest_dir,
        )

        if not r1_path.is_file():
            raise FileNotFoundError(
                f"Row {line_number} R1 FASTQ does not exist: "
                f"{r1_path}"
            )

        if not r2_path.is_file():
            raise FileNotFoundError(
                f"Row {line_number} R2 FASTQ does not exist: "
                f"{r2_path}"
            )

        metadata["r1"] = str(r1_path)
        metadata["r2"] = str(r2_path)

        sample = Sample(
            sample_id=sample_id,
            r1=r1_path,
            r2=r2_path,
            genus=_optional_value(metadata, "genus"),
            species=_optional_value(metadata, "species"),
            source=_optional_value(metadata, "source"),
            metadata=metadata,
        )
        samples.append(sample)

        if logger is not None:
            logger.info(
                "[%s] Validated paired FASTQ inputs and retained "
                "%d metadata fields.",
                sample_id,
                len(sample.metadata),
            )
            logger.debug(
                "[%s] Manifest metadata: %s",
                sample_id,
                dict(sample.metadata),
            )

    if logger is not None:
        logger.info(
            "Validated %d samples from %s.",
            len(samples),
            manifest_path,
        )

    return samples


def _row_metadata(row: pd.Series) -> dict[str, str]:
    """Return all nonblank values in one manifest row."""
    metadata: dict[str, str] = {}

    for column, value in row.items():
        key = str(column).strip()
        text = str(value).strip()

        if not key or not text:
            continue

        metadata[key] = text

    return metadata


def _resolve_manifest_path(
    value: str,
    manifest_dir: Path,
) -> Path:
    """Resolve an absolute or manifest-relative path."""
    path = Path(str(value).strip()).expanduser()

    if path.is_absolute():
        return path.resolve()

    return (manifest_dir / path).resolve()


def _optional_value(
    metadata: dict[str, str],
    column_name: str,
) -> str | None:
    """Return one optional metadata value."""
    value = metadata.get(column_name)
    return value if value else None
