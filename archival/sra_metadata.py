"""Build reviewable NCBI SRA metadata tables from runtime manifests."""

from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd


SRA_COLUMNS = [
    "sample_name",
    "library_ID",
    "title",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "platform",
    "instrument_model",
    "design_description",
    "filetype",
    "filename",
    "filename2",
    "organism",
    "missing_fields",
    "review_status",
]

REQUIRED_REVIEW_FIELDS = [
    "sample_name",
    "library_ID",
    "title",
    "library_strategy",
    "library_source",
    "library_selection",
    "library_layout",
    "platform",
    "instrument_model",
    "filetype",
    "filename",
]


def _clean(value: object) -> str:
    """Return a normalized string, treating pandas missing values as blank."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _first_value(
    row: pd.Series,
    names: tuple[str, ...],
    default: str = "",
) -> str:
    """Return the first nonblank value found among candidate column names."""
    for name in names:
        if name in row.index:
            value = _clean(row[name])
            if value:
                return value
    return default


def _organism_name(row: pd.Series) -> str:
    """Build a binomial name from organism or genus/species columns."""
    organism = _first_value(
        row,
        ("organism", "scientific_name"),
    )
    if organism:
        return organism

    genus = _first_value(row, ("genus",))
    species = _first_value(row, ("species",))
    return " ".join(
        value
        for value in (genus, species)
        if value
    )


def _raw_fastq_path(row: pd.Series, column: str) -> str:
    """Return an absolute raw FASTQ path from the runtime manifest."""
    value = _clean(row.get(column, ""))
    if not value:
        return ""
    return str(Path(value).expanduser().resolve())


def build_sra_metadata(
    runtime_manifest_path: str | Path,
    defaults: dict[str, object] | None = None,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Build one reviewable SRA metadata row per raw sequencing sample.

    Manifest values take precedence over configuration defaults. Missing
    submission fields are retained as blank values and listed in
    ``missing_fields`` rather than causing the export to fail.
    """
    runtime_manifest_path = Path(runtime_manifest_path)
    defaults = defaults or {}

    if not runtime_manifest_path.exists():
        raise FileNotFoundError(
            f"Runtime manifest does not exist: {runtime_manifest_path}"
        )

    table = pd.read_csv(
        runtime_manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    required_manifest_columns = {"sample_id", "r1", "r2"}
    missing_manifest_columns = (
        required_manifest_columns
        - set(table.columns)
    )
    if missing_manifest_columns:
        raise ValueError(
            "Runtime manifest is missing required columns: "
            f"{sorted(missing_manifest_columns)}"
        )

    records: list[dict[str, str]] = []

    for _, row in table.iterrows():
        sample_id = _first_value(row, ("sample_id",))
        if not sample_id:
            raise ValueError(
                "Runtime manifest contains a blank sample_id."
            )

        library_id = _first_value(
            row,
            ("library_ID", "library_id"),
            default=sample_id,
        )

        record = {
            "sample_name": _first_value(
                row,
                ("sample_name", "biosample", "sample_id"),
                default=sample_id,
            ),
            "library_ID": library_id,
            "title": _first_value(
                row,
                ("title", "library_title"),
                default=str(
                    defaults.get(
                        "title_template",
                        "{sample_id} raw sequencing reads",
                    )
                ).format(
                    sample_id=sample_id,
                    library_id=library_id,
                ),
            ),
            "library_strategy": _first_value(
                row,
                ("library_strategy",),
                default=_clean(
                    defaults.get("library_strategy", "")
                ),
            ),
            "library_source": _first_value(
                row,
                ("library_source",),
                default=_clean(
                    defaults.get("library_source", "")
                ),
            ),
            "library_selection": _first_value(
                row,
                ("library_selection",),
                default=_clean(
                    defaults.get("library_selection", "")
                ),
            ),
            "library_layout": _first_value(
                row,
                ("library_layout",),
                default=_clean(
                    defaults.get("library_layout", "PAIRED")
                ),
            ),
            "platform": _first_value(
                row,
                ("platform",),
                default=_clean(
                    defaults.get("platform", "")
                ),
            ),
            "instrument_model": _first_value(
                row,
                ("instrument_model",),
                default=_clean(
                    defaults.get("instrument_model", "")
                ),
            ),
            "design_description": _first_value(
                row,
                ("design_description",),
                default=_clean(
                    defaults.get("design_description", "")
                ),
            ),
            "filetype": _first_value(
                row,
                ("filetype", "file_type"),
                default=_clean(
                    defaults.get("filetype", "fastq")
                ),
            ),
            "filename": _raw_fastq_path(row, "r1"),
            "filename2": _raw_fastq_path(row, "r2"),
            "organism": _organism_name(row),
        }

        missing = [
            field
            for field in REQUIRED_REVIEW_FIELDS
            if not record[field]
        ]

        if (
            record["library_layout"].upper() == "PAIRED"
            and not record["filename2"]
        ):
            missing.append("filename2")

        record["missing_fields"] = ";".join(
            sorted(set(missing))
        )
        record["review_status"] = (
            "READY"
            if not missing
            else "MANUAL_REVIEW_REQUIRED"
        )
        records.append(record)

    result = pd.DataFrame(
        records,
        columns=SRA_COLUMNS,
    )

    if logger is not None:
        review_count = int(
            (
                result["review_status"]
                == "MANUAL_REVIEW_REQUIRED"
            ).sum()
        )
        logger.info(
            "Built SRA metadata for %d samples; "
            "%d require manual review.",
            len(result),
            review_count,
        )

    return result


def write_sra_metadata(
    runtime_manifest_path: str | Path,
    output_path: str | Path,
    defaults: dict[str, object] | None = None,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Build and write a tab-delimited SRA metadata table."""
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table = build_sra_metadata(
        runtime_manifest_path=runtime_manifest_path,
        defaults=defaults,
        logger=logger,
    )
    table.to_csv(
        output_path,
        sep="\t",
        index=False,
    )

    if logger is not None:
        logger.info(
            "Wrote SRA metadata table to %s.",
            output_path,
        )

    return table
