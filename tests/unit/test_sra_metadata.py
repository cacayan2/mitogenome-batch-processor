"""Unit tests for SRA metadata generation."""

from pathlib import Path

import pandas as pd

from mitopipeline.archival.sra_metadata import (
    build_sra_metadata,
    write_sra_metadata,
)


def _write_manifest(tmp_path: Path) -> Path:
    """Create a representative runtime manifest."""
    r1 = tmp_path / "sample_001_R1.fastq.gz"
    r2 = tmp_path / "sample_001_R2.fastq.gz"
    r1.touch()
    r2.touch()

    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "genus": "Lepomis",
                "species": "macrochirus",
                "r1": str(r1),
                "r2": str(r2),
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )
    return manifest


def test_build_sra_metadata_uses_defaults(
        tmp_path: Path,
):
    """Defaults populate submission fields."""
    manifest = _write_manifest(tmp_path)

    table = build_sra_metadata(
        runtime_manifest_path=manifest,
        defaults={
            "library_strategy": "WGS",
            "library_source": "GENOMIC",
            "library_selection": "RANDOM",
            "library_layout": "PAIRED",
            "platform": "ILLUMINA",
            "instrument_model": "Illumina NovaSeq 6000",
        },
    )

    assert len(table) == 1
    row = table.iloc[0]

    assert row["sample_name"] == "sample_001"
    assert row["library_ID"] == "sample_001"
    assert row["organism"] == "Lepomis macrochirus"
    assert row["filename"].endswith(
        "sample_001_R1.fastq.gz"
    )
    assert row["filename2"].endswith(
        "sample_001_R2.fastq.gz"
    )
    assert row["review_status"] == "READY"
    assert row["missing_fields"] == ""


def test_manifest_values_override_defaults(
        tmp_path: Path,
):
    """Per-sample values override shared defaults."""
    manifest = _write_manifest(tmp_path)
    table = pd.read_csv(
        manifest,
        sep="\t",
    )
    table["library_strategy"] = "AMPLICON"
    table.to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    result = build_sra_metadata(
        runtime_manifest_path=manifest,
        defaults={
            "library_strategy": "WGS",
        },
    )

    assert (
        result.iloc[0]["library_strategy"]
        == "AMPLICON"
    )


def test_missing_fields_are_flagged(
        tmp_path: Path,
):
    """Incomplete metadata remains reviewable."""
    manifest = _write_manifest(tmp_path)

    table = build_sra_metadata(
        runtime_manifest_path=manifest,
    )
    row = table.iloc[0]

    assert (
        row["review_status"]
        == "MANUAL_REVIEW_REQUIRED"
    )
    assert "platform" in row["missing_fields"]
    assert "instrument_model" in row["missing_fields"]


def test_write_sra_metadata_creates_tsv(
        tmp_path: Path,
):
    """Writer creates the expected output file."""
    manifest = _write_manifest(tmp_path)
    output = (
        tmp_path
        / "submission"
        / "sra"
        / "sra_metadata.tsv"
    )

    write_sra_metadata(
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
