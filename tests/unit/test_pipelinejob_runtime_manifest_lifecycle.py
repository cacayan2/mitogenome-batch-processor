"""Tests for PipelineJob lifecycle with deferred samples."""

from pathlib import Path
import json

from mitopipeline.models.pipeline_job import PipelineJob


def test_pipeline_job_allows_deferred_samples(tmp_path: Path):
    """PipelineJob can be created before samples are known."""
    job = PipelineJob(
        parent_dir=tmp_path,
    )

    assert job.samples == []

    job.set_samples(
        ["sample_001"]
    )
    job.mark_created()

    metadata = json.loads(
        (
            job.job_dir
            / "job_metadata.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert metadata["sample_count"] == 1
    assert metadata["samples"] == ["sample_001"]
