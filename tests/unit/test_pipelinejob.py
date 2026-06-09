"""test_pipelinejob.py

Contains unit tests for the PipelineRun class. 
"""
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

    # Instantiating the PipelineJob object.
    job = PipelineJob(test_path)
    
    # Assertions for job directory creation.
    assert job._job_dir.exists()
    assert (job._job_dir / "annotation").exists()
    assert (job._job_dir / "assembly").exists()
    assert (job._job_dir / "logs").exists()
    assert (job._job_dir / "phylogeny").exists()
    assert (job._job_dir / "qc").exists()
    assert (job._job_dir / "reports").exists()
    assert (job._job_dir / "stats").exists()
    assert (job._job_dir / "submission").exists()
    assert (job._job_dir / "trimming").exists()

    # Assertions for job object behavior.
    assert job._job_id
    assert job._start_time
    assert job._end_time is None
    assert job._failed_time is None
    assert job._is_new_job
    assert job._job_logger

    # Assertions for .json metadata.
    assert (job._job_dir / "job_metadata.json").exists()
    with open(job._job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["job_id"] == job._job_id
    assert Path(data["output_dir"]) == job._job_dir
    assert data["status"] == "created"
    
    # Assertions for completion behavior.
    job.mark_completed()
    with open(job._job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "completed"

    # Assertions for job failure.
    job.mark_failed()
    with open(job._job_dir / "job_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "failed"

    

