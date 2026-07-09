"""test_run_report_data.py

Unit tests for run-level report-data aggregation.
"""

# Imports
import json
from pathlib import Path

from mitopipeline.reporting.run_report_data import (
    collect_run_report_data,
    collect_sample_run_status,
    get_manifest_sample_ids,
    sample_stage_done_path,
)


def create_run_report_fixture(job_directory: Path) -> None:
    """Create a small run-report fixture."""
    (job_directory / "metadata").mkdir(parents=True)
    (job_directory / "metadata" / "runtime_manifest.tsv").write_text(
        (
            "sample_id\tr1\tr2\tgenus\tspecies\n"
            "sample_001\t/a_R1.fastq.gz\t/a_R2.fastq.gz\tGenus\tone\n"
            "sample_002\t/b_R1.fastq.gz\t/b_R2.fastq.gz\tGenus\ttwo\n"
        ),
        encoding="utf-8",
    )
    (job_directory / "metadata" / "job_metadata.json").write_text(
        json.dumps({"start_time": "2026-07-08T10:00:00", "end_time": "2026-07-08T11:00:00", "runtime_seconds": 3600}),
        encoding="utf-8",
    )

    for sample_id in ["sample_001", "sample_002"]:
        (job_directory / "reporting").mkdir(parents=True, exist_ok=True)
        (job_directory / "reporting" / f"{sample_id}.report.md").write_text(f"# {sample_id}\n", encoding="utf-8")

    for sample_id in ["sample_001", "sample_002"]:
        for path in [
            job_directory / "trimming" / f"{sample_id}.trimming.done",
            job_directory / "assembly" / f"{sample_id}.assembly.done",
        ]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    annotation_done = job_directory / "annotation" / "sample_001.annotation.done"
    annotation_done.parent.mkdir(parents=True, exist_ok=True)
    annotation_done.touch()


def test_sample_stage_done_path(tmp_path: Path):
    """Confirm stage done paths are generated."""
    result = sample_stage_done_path(
        job_directory=tmp_path,
        sample_id="sample_001",
        stage_name="assembly",
    )
    assert result == tmp_path / "assembly" / "sample_001.assembly.done"


def test_get_manifest_sample_ids(tmp_path: Path):
    """Confirm sample IDs are read from the runtime manifest."""
    create_run_report_fixture(tmp_path)
    assert get_manifest_sample_ids(tmp_path / "metadata" / "runtime_manifest.tsv") == ["sample_001", "sample_002"]


def test_collect_sample_run_status(tmp_path: Path):
    """Confirm sample stage status is summarized."""
    create_run_report_fixture(tmp_path)
    status = collect_sample_run_status(
        sample_id="sample_002",
        job_directory=tmp_path,
        enabled_stages=["trimming", "assembly", "annotation"],
    )
    assert status.overall_status == "incomplete"
    assert status.failed_stages == ["annotation"]


def test_collect_run_report_data(tmp_path: Path):
    """Confirm run data aggregates samples and stage totals."""
    create_run_report_fixture(tmp_path)
    run_data = collect_run_report_data(
        job_id="test_job",
        job_directory=tmp_path,
        enabled_stages=["trimming", "assembly", "annotation", "reporting"],
    )
    assert run_data.job_id == "test_job"
    assert run_data.total_samples == 2
    assert run_data.stage_totals["trimming"]["complete"] == 2
    assert run_data.stage_totals["annotation"]["missing"] == 1
    assert run_data.run_metadata["runtime_seconds"] == 3600
