"""Unit tests for archival readiness validation."""

from pathlib import Path

import pandas as pd

from mitopipeline.archival.validation import (
    render_validation_report,
    validate_archival_readiness,
    write_archival_validation_outputs,
)


def _write_complete_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Create a complete archival validation fixture."""
    job_directory = tmp_path / "job"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    r1 = raw_dir / "sample_001_R1.fastq.gz"
    r2 = raw_dir / "sample_001_R2.fastq.gz"
    r1.touch()
    r2.touch()

    manifest = job_directory / "metadata" / "runtime_manifest.tsv"
    manifest.parent.mkdir(parents=True)
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

    assembly = job_directory / "assembly"
    annotation = job_directory / "annotation" / "sample_001"
    assembly.mkdir(parents=True)
    annotation.mkdir(parents=True)

    (assembly / "sample_001.fasta").write_text(
        ">sample_001\nACGT\n",
        encoding="utf-8",
    )

    for filename in ["result.gff", "result.fas", "result.tbl", "result.bed"]:
        (annotation / filename).write_text(
            "fixture\n",
            encoding="utf-8",
        )

    submission = job_directory / "submission"

    biosample = submission / "biosample" / "biosample_metadata.tsv"
    biosample.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "sample_name": "sample_001",
                "organism": "Lepomis macrochirus",
                "review_status": "READY",
                "missing_fields": "",
            }
        ]
    ).to_csv(
        biosample,
        sep="\t",
        index=False,
    )

    sra = submission / "sra" / "sra_metadata.tsv"
    sra.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "sample_name": "sample_001",
                "review_status": "READY",
                "missing_fields": "",
                "filename": str(r1),
                "filename2": str(r2),
            }
        ]
    ).to_csv(
        sra,
        sep="\t",
        index=False,
    )

    mito = submission / "mitogenomes" / "mitogenome_metadata.tsv"
    mito.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "review_status": "READY",
                "missing_files": "",
                "missing_metadata": "",
            }
        ]
    ).to_csv(
        mito,
        sep="\t",
        index=False,
    )

    return manifest, job_directory


def test_validate_archival_readiness_complete_sample(tmp_path: Path):
    """Complete sample is marked ready."""
    manifest, job_directory = _write_complete_fixture(tmp_path)

    table = validate_archival_readiness(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
    )

    assert len(table) == 1
    assert bool(table.iloc[0]["ready_for_review"]) is True
    assert table.iloc[0]["submission_blockers"] == ""


def test_validate_archival_readiness_reports_missing_files(tmp_path: Path):
    """Missing files and metadata are reported."""
    job_directory = tmp_path / "job"
    manifest = job_directory / "metadata" / "runtime_manifest.tsv"
    manifest.parent.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "r1": str(tmp_path / "missing_R1.fastq.gz"),
                "r2": str(tmp_path / "missing_R2.fastq.gz"),
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    table = validate_archival_readiness(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
    )

    row = table.iloc[0]
    assert bool(row["ready_for_review"]) is False
    assert "Missing raw FASTQ" in row["submission_blockers"]
    assert "organism" in row["missing_metadata"]


def test_render_validation_report_contains_summary(tmp_path: Path):
    """Markdown report includes summary and sample status."""
    manifest, job_directory = _write_complete_fixture(tmp_path)
    table = validate_archival_readiness(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
    )

    report = render_validation_report(table)

    assert "# NCBI archival validation report" in report
    assert "Ready for review: 1" in report
    assert "sample_001" in report


def test_write_archival_validation_outputs(tmp_path: Path):
    """Writer creates TSV summary and Markdown report."""
    manifest, job_directory = _write_complete_fixture(tmp_path)

    summary = job_directory / "submission" / "validation_summary.tsv"
    report = job_directory / "submission" / "validation_report.md"

    write_archival_validation_outputs(
        runtime_manifest_path=manifest,
        job_directory=job_directory,
        summary_output_path=summary,
        report_output_path=report,
    )

    assert summary.exists()
    assert report.exists()
