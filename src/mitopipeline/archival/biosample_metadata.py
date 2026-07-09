"""Build reviewable NCBI BioSample metadata tables."""

from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd


BIOSAMPLE_COLUMNS = [
    "sample_name",
    "bioproject_accession",
    "organism",
    "isolate",
    "breed",
    "host",
    "isolation_source",
    "collection_date",
    "geo_loc_name",
    "lat_lon",
    "sample_type",
    "tissue",
    "sex",
    "dev_stage",
    "description",
    "missing_fields",
    "review_status",
]

REQUIRED_REVIEW_FIELDS = [
    "sample_name",
    "organism",
    "collection_date",
    "geo_loc_name",
    "isolation_source",
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
    """Return the first nonblank value among candidate columns."""
    for name in names:
        if name in row.index:
            value = _clean(row[name])
            if value:
                return value
    return default


def _organism_name(row: pd.Series) -> str:
    """Build organism from organism/scientific_name or genus/species."""
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


def build_biosample_metadata(
    runtime_manifest_path: str | Path,
    defaults: dict[str, object] | None = None,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Build one reviewable BioSample metadata row per biological sample.

    Manifest values take precedence over shared defaults. Missing required
    biological metadata does not fail export; it is listed in
    ``missing_fields`` so the PI can review and complete the table.
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

    if "sample_id" not in table.columns:
        raise ValueError(
            "Runtime manifest is missing required column: sample_id"
        )

    records: list[dict[str, str]] = []

    for _, row in table.iterrows():
        sample_id = _first_value(row, ("sample_id",))
        if not sample_id:
            raise ValueError(
                "Runtime manifest contains a blank sample_id."
            )

        organism = _organism_name(row)

        record = {
            "sample_name": _first_value(
                row,
                ("sample_name", "biosample", "sample_id"),
                default=sample_id,
            ),
            "bioproject_accession": _first_value(
                row,
                ("bioproject_accession", "bioproject"),
                default=_clean(
                    defaults.get("bioproject_accession", "")
                ),
            ),
            "organism": organism,
            "isolate": _first_value(
                row,
                ("isolate",),
                default=_clean(defaults.get("isolate", "")),
            ),
            "breed": _first_value(
                row,
                ("breed",),
                default=_clean(defaults.get("breed", "")),
            ),
            "host": _first_value(
                row,
                ("host",),
                default=_clean(defaults.get("host", "")),
            ),
            "isolation_source": _first_value(
                row,
                ("isolation_source", "source"),
                default=_clean(
                    defaults.get("isolation_source", "")
                ),
            ),
            "collection_date": _first_value(
                row,
                ("collection_date", "collection_date_utc"),
                default=_clean(
                    defaults.get("collection_date", "")
                ),
            ),
            "geo_loc_name": _first_value(
                row,
                ("geo_loc_name", "geographic_location"),
                default=_clean(
                    defaults.get("geo_loc_name", "")
                ),
            ),
            "lat_lon": _first_value(
                row,
                ("lat_lon", "latitude_longitude"),
                default=_clean(defaults.get("lat_lon", "")),
            ),
            "sample_type": _first_value(
                row,
                ("sample_type",),
                default=_clean(
                    defaults.get("sample_type", "")
                ),
            ),
            "tissue": _first_value(
                row,
                ("tissue",),
                default=_clean(defaults.get("tissue", "")),
            ),
            "sex": _first_value(
                row,
                ("sex",),
                default=_clean(defaults.get("sex", "")),
            ),
            "dev_stage": _first_value(
                row,
                ("dev_stage", "developmental_stage"),
                default=_clean(defaults.get("dev_stage", "")),
            ),
            "description": _first_value(
                row,
                ("description", "sample_description"),
                default=str(
                    defaults.get(
                        "description_template",
                        "Biological sample for {sample_id}.",
                    )
                ).format(
                    sample_id=sample_id,
                    organism=organism or "unknown organism",
                ),
            ),
        }

        missing = [
            field
            for field in REQUIRED_REVIEW_FIELDS
            if not record[field]
        ]

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
        columns=BIOSAMPLE_COLUMNS,
    )

    if logger is not None:
        review_count = int(
            (
                result["review_status"]
                == "MANUAL_REVIEW_REQUIRED"
            ).sum()
        )
        logger.info(
            "Built BioSample metadata for %d samples; "
            "%d require manual review.",
            len(result),
            review_count,
        )

    return result


def write_biosample_metadata(
    runtime_manifest_path: str | Path,
    output_path: str | Path,
    defaults: dict[str, object] | None = None,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Build and write a tab-delimited BioSample metadata table."""
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table = build_biosample_metadata(
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
            "Wrote BioSample metadata table to %s.",
            output_path,
        )

    return table
