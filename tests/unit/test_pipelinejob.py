"""test_pipelinejob.py

Contains unit tests for the PipelineRun class. 
"""
from pathlib import Path
from mitopipeline import logging
from mitopipeline.models.pipeline_job import PipelineJob
import shutil

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

    

    # Assertions
    assert job._job_id

    # Remove parent directory upon completion of unit tests. 
    if Path.exists(test_path):
        shutil.rmtree(test_path)

    

