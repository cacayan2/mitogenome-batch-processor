"""test_pipelinejob.py

Contains unit tests for the PipelineRun class. 
"""

# Imports
from pathlib import Path
from mitopipeline.models.pipeline_job import PipelineJob
import shutil
import json

def test_pipelinejob():
    """Unit tests for PipelineRun class."""
    # Specifying a parent directory for testing job directory creation.
    test_path = Path("pipelinerun_tmp")
    
    # Creating the parent directory.
    if Path.exists(test_path):
        shutil.rmtree(test_path)
    test_path.mkdir(parents = True, exist_ok = True)

    # Instantiating the PipelineJob object and artificially inserting samples.
    sample_ids = ["sample_001", "sample_002"]
    job = PipelineJob(test_path, samples = sample_ids)
    
    # Assertions for job directory creation.
    assert job.job_dir.exists()
    assert (job.job_dir / "annotation").exists()
    assert (job.job_dir / "assembly").exists()
    assert (job.job_dir / "logs").exists()
    assert (job.job_dir / "phylogeny").exists()
    assert (job.job_dir / "qc").exists()
    assert (job.job_dir / "reports").exists()
    assert (job.job_dir / "stats").exists()
    assert (job.job_dir / "submission").exists()
    assert (job.job_dir / "trimming").exists()

    # Assertions for job object behavior.
    assert job.job_id
    assert job.start_time
    assert job.end_time is None
    assert job.failed_time is None
    assert job.is_new_job
    assert job.job_logger

    # Assertions for .json metadata.
    assert (job.job_dir / "job_metadata.json").exists()
    with open(job.job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["job_id"] == job.job_id
    assert Path(data["output_dir"]) == job.job_dir
    assert data["status"] == "created"
    assert data["sample_count"] == 2
    assert data["samples"] == sample_ids
    
    # Assertions for completion behavior.
    job.mark_completed()
    with open(job.job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "completed"
    assert data["sample_count"] == 2
    assert data["samples"] == sample_ids

    # Assertions for job failure.
    job.mark_failed()
    with open(job.job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "failed"
    assert data["sample_count"] == 2
    assert data["samples"] == sample_ids

    # Deleting the parent directory.
    if Path.exists(test_path):
        shutil.rmtree(test_path)


