"""Unit tests for mitogenome submission CLI."""

import json
from pathlib import Path
import sys

import pandas as pd

from mitopipeline.exec import prepare_mitogenome_submission


def test_main_writes_mitogenome_submission(
        tmp_path: Path,
        monkeypatch,
):
    """CLI writes metadata and copies files."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "organism": "Lepomis macrochirus",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    job_directory = tmp_path / "job"
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
        ">sample_001\nACGT\n",
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
            "fixture\n",
            encoding="utf-8",
        )

    output_directory = (
        job_directory
        / "submission"
        / "mitogenomes"
    )
    metadata_output = (
        output_directory
        / "mitogenome_metadata.tsv"
    )
    log_file = tmp_path / "mitogenome_submission.log"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare_mitogenome_submission",
            "--runtime-manifest",
            str(manifest),
            "--job-directory",
            str(job_directory),
            "--output-directory",
            str(output_directory),
            "--metadata-output",
            str(metadata_output),
            "--defaults-json",
            json.dumps(
                {
                    "assembly_method": "GetOrganelle",
                    "annotation_method": "MITOS2",
                }
            ),
            "--log-file",
            str(log_file),
        ],
    )

    assert prepare_mitogenome_submission.main() == 0
    assert metadata_output.exists()
