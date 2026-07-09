"""Unit tests for BioSample metadata generation."""

from pathlib import Path

import pandas as pd

from mitopipeline.archival.biosample_metadata import (
    build_biosample_metadata,
    write_biosample_metadata,
)


def _write_manifest(tmp_path: Path) -> Path:
    """Create a representative runtime manifest."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "genus": "Lepomis",
                "species": "macrochirus",
                "source": "eDNA water filter",
                "collection_date": "2026-06-15",
                "geo_loc_name": "USA: Illinois, Fox River",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )
    return manifest


def test_build_biosample_metadata_from_manifest(
        tmp_path: Path,
):
    """Manifest fields populate BioSample metadata."""
    manifest = _write_manifest(tmp_path)

    table = build_biosample_metadata(
        runtime_manifest_path=manifest,
    )

    assert len(table) == 1
    row = table.iloc[0]

    assert row["sample_name"] == "sample_001"
    assert row["organism"] == "Lepomis macrochirus"
    assert row["isolation_source"] == "eDNA water filter"
    assert row["collection_date"] == "2026-06-15"
    assert row["geo_loc_name"] == "USA: Illinois, Fox River"
    assert row["review_status"] == "READY"
    assert row["missing_fields"] == ""


def test_defaults_fill_biosample_fields(
        tmp_path: Path,
):
    """Shared defaults fill missing collection fields."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "genus": "Lepomis",
                "species": "macrochirus",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    table = build_biosample_metadata(
        runtime_manifest_path=manifest,
        defaults={
            "isolation_source": "eDNA water filter",
            "collection_date": "2026-06",
            "geo_loc_name": "USA: Illinois",
            "sample_type": "environmental sample",
        },
    )

    row = table.iloc[0]
    assert row["isolation_source"] == "eDNA water filter"
    assert row["collection_date"] == "2026-06"
    assert row["geo_loc_name"] == "USA: Illinois"
    assert row["sample_type"] == "environmental sample"
    assert row["review_status"] == "READY"


def test_missing_required_biosample_fields_are_flagged(
        tmp_path: Path,
):
    """Incomplete biological metadata remains reviewable."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "genus": "",
                "species": "",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    table = build_biosample_metadata(
        runtime_manifest_path=manifest,
    )
    row = table.iloc[0]

    assert (
        row["review_status"]
        == "MANUAL_REVIEW_REQUIRED"
    )
    assert "organism" in row["missing_fields"]
    assert "collection_date" in row["missing_fields"]
    assert "geo_loc_name" in row["missing_fields"]


def test_manifest_values_override_defaults(
        tmp_path: Path,
):
    """Per-sample manifest values override shared defaults."""
    manifest = _write_manifest(tmp_path)

    table = build_biosample_metadata(
        runtime_manifest_path=manifest,
        defaults={
            "geo_loc_name": "USA: Default",
        },
    )

    assert (
        table.iloc[0]["geo_loc_name"]
        == "USA: Illinois, Fox River"
    )


def test_write_biosample_metadata_creates_tsv(
        tmp_path: Path,
):
    """Writer creates the expected output file."""
    manifest = _write_manifest(tmp_path)
    output = (
        tmp_path
        / "submission"
        / "biosample"
        / "biosample_metadata.tsv"
    )

    write_biosample_metadata(
        runtime_manifest_path=manifest,
        output_path=output,
    )

    assert output.exists()
    written = pd.read_csv(
        output,
        sep="\t",
        keep_default_na=False,
    )
    assert len(written) == 1
