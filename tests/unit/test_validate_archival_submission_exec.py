"""Unit tests for archival validation CLI."""

from pathlib import Path
import sys

import pandas as pd

from mitopipeline.exec import validate_archival_submission


def test_main_writes_validation_outputs(
        tmp_path: Path,
        monkeypatch,
):
    """CLI writes validation summary and report."""
    job_directory = tmp_path / "job"
    manifest = job_directory / "metadata" / "runtime_manifest.tsv"
    manifest.parent.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "r1": str(tmp_path / "R1.fastq.gz"),
                "r2": str(tmp_path / "R2.fastq.gz"),
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    summary = job_directory / "submission" / "validation_summary.tsv"
    report = job_directory / "submission" / "validation_report.md"
    log_file = job_directory / "logs" / "validation.log"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_archival_submission",
            "--runtime-manifest",
            str(manifest),
            "--job-directory",
            str(job_directory),
            "--summary-output",
            str(summary),
            "--report-output",
            str(report),
            "--log-file",
            str(log_file),
        ],
    )

    assert validate_archival_submission.main() == 0
    assert summary.exists()
    assert report.exists()
