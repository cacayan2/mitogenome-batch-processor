"""Unit tests for mitogenome submission preparation."""

from pathlib import Path

import pandas as pd

from mitopipeline.archival.mitogenome_metadata import (
    build_mitogenome_submission,
    write_mitogenome_submission,
)


def _write_runtime_manifest(
        tmp_path: Path,
) -> Path:
    """Create runtime manifest fixture."""
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
    return manifest


def _write_pipeline_outputs(
        job_directory: Path,
) -> None:
    """Create assembly and MITOS2 output fixtures."""
    assembly_dir = job_directory / "assembly"
    annotation_dir = (
        job_directory
        / "annotation"
        / "sample_001"
    )

    assembly_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    annotation_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        assembly_dir
        / "sample_001.fasta"
    ).write_text(
        ">sample_001\nACGTACGTACGT\n",
        encoding="utf-8",
    )

    for filename in [
        "result.gff",
        "result.fas",
        "result.tbl",
        "result.bed",
    ]:
        (
            annotation_dir
            / filename
        ).write_text(
            f"{filename}\n",
            encoding="utf-8",
        )


def test_build_mitogenome_submission_copies_files(
        tmp_path: Path,
):
    """Assembly and annotation outputs are collected."""
    manifest = _write_runtime_manifest(tmp_path)
    job_directory = tmp_path / "job"
    output_directory = (
        job_directory
        / "submission"
        / "mitogenomes"
    )
    _write_pipeline_outputs(job_directory)

    table = build_mitogenome_submission(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
        output_directory=output_directory,
    )

    assert len(table) == 1
    row = table.iloc[0]

    assert row["sample_id"] == "sample_001"
    assert row["organism"] == "Lepomis macrochirus"
    assert row["sequence_length_bp"] == "12"
    assert row["review_status"] == "READY"
    assert row["missing_files"] == ""
    assert Path(row["assembly_fasta"]).exists()
    assert Path(row["annotation_gff"]).exists()


def test_missing_outputs_are_flagged(
        tmp_path: Path,
):
    """Missing assembly/annotation outputs are reported clearly."""
    manifest = _write_runtime_manifest(tmp_path)
    job_directory = tmp_path / "job"
    output_directory = (
        job_directory
        / "submission"
        / "mitogenomes"
    )

    table = build_mitogenome_submission(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
        output_directory=output_directory,
    )

    row = table.iloc[0]
    assert (
        row["review_status"]
        == "MANUAL_REVIEW_REQUIRED"
    )
    assert "sample_001.fasta" in row["missing_files"]
    assert "result.gff" in row["missing_files"]


def test_missing_organism_is_flagged(
        tmp_path: Path,
):
    """Missing organism metadata requires manual review."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    job_directory = tmp_path / "job"
    _write_pipeline_outputs(job_directory)

    table = build_mitogenome_submission(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
        output_directory=(
            job_directory
            / "submission"
            / "mitogenomes"
        ),
    )

    row = table.iloc[0]
    assert (
        row["review_status"]
        == "MANUAL_REVIEW_REQUIRED"
    )
    assert "organism" in row["missing_metadata"]


def test_write_mitogenome_submission_creates_metadata_tsv(
        tmp_path: Path,
):
    """Writer creates mitogenome metadata table."""
    manifest = _write_runtime_manifest(tmp_path)
    job_directory = tmp_path / "job"
    output_directory = (
        job_directory
        / "submission"
        / "mitogenomes"
    )
    _write_pipeline_outputs(job_directory)

    output = (
        output_directory
        / "mitogenome_metadata.tsv"
    )

    write_mitogenome_submission(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
        output_directory=output_directory,
        metadata_output_path=output,
    )

    assert output.exists()
    written = pd.read_csv(
        output,
        sep="\t",
        keep_default_na=False,
    )
    assert len(written) == 1
