"""pipeline_job.py

This module contains the PipelineJob class - a PipelineJob object exists for the lifetime of a pipeline run, and contains important metadata about the run.

"""

# Imports
from datetime import datetime
from mitopipeline.logging.logger_factory import make_logger
from pathlib import Path
import logging
import uuid
import json

class PipelineRun():
    """Manages the lifecycle and job metadata for a pipeline run.

    This class handles the creation of a job directory, logging, and job metadata. 
    It generates a unique job ID if one is not provided, and creates a logger for the job.
    """
    def __init__(self, parent_dir: Path, job_id: str = None):
        """Initializes a PipelineRun object.

        Creates a unique job ID if one is not provided, and creates a logger for the job. 
        Creates a job directory in the specified parent directory.

        Args:
            parent_dir (Path): The parent directory for the job directory.
            job_id (str, optional): The job ID. Defaults to None and will be generated if not provided. 
        """
        # Setting default value for is a new job to True - this will change in subsequent logic structures. 
        self._is_new_job = True
        
        # Verifying if the job exists. Pipeline will either progress where last job left off or start a new job.
        if job_id is not None:
            self._is_new_job = False
            self._job_id = job_id
        # Else branch assigns a new job ID for the job.
        else:
            now = datetime.now()
            self._job_id = f"{now.strftime("%Y%m%d")}_{now.strftime("%H%M")}_{str(uuid.uuid4())}"

        # Instantiation of member variables. 
        self._start_time = datetime.now()
        self._end_time = None
        self._runtime = None
        self._parent_dir = parent_dir
        self._job_dir = self._parent_dir / self._job_id
        self._job_logger = self.create_output_directory(self)
        self._job_logger.info(f"Pipeline job {self._job_id} started at {self._start_time}.")
        
        # Sends information about the job to the logger. 
        if self._is_new_job:
            self._job_logger.info(f"Pipeline job {self._job_id} is a new job, new directory was successfully created at {self._job_dir}.")
        else:
            self._job_logger.info(f"Pipeline job {self._job_id} already exists, using existing directory and automatically progressing pipeline from previous run ({self._job_dir}).")
            
        
    def create_output_directory(self) -> logging.Logger:
        """Upon instantiation of a PipelineJob object, this method will create a job directory in the specified parent directory.

        Returns:
            logging.Logger: A logger for the job.
        """
        # Parent directory must exist - if it doesn't raise an error (job object is not created).
        if not self._parent_dir.exists():
            raise FileNotFoundError(f"Failed to find parent directory specified: {self.parent_dir}, stopping pipeline execution.")
        if not self._job_dir.exists():
            self._job_dir.mkdir(parents = True, exist_ok = True)
            
            dirs = [
                self._job_dir / "logs",
                self._job_dir / "qc",
                self._job_dir / "trimming",
                self._job_dir / "assembly",
                self._job_dir / "annotation",
                self._job_dir / "phylogeny",
                self._job_dir / "reports",
                self._job_dir / "stats",
                self._job_dir / "submission"
            ]
            
            for dir in dirs:
                if not dir.exists():
                    dir.mkdir(parents = True, exist_ok = True)
    
            job_logger = make_logger(name = self._job_id, log_file_path = self._job_dir / "logs" / f"pipeline_job.log")

            return job_logger
    
    def mark_created(self):
        """Marks the pipeline job as created and records associated metadata.
        """

    def mark_completed(self):
        """Marks the pipeline job as completed and records associated metadata.
        """
        self._end_time = datetime.now()
        self._runtime = self._end_time - self._start_time
        data = {
            "job_id": self._job_id,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "runtime (seconds)": self._runtime.total_seconds(),
            "output_dir": self._job_dir,
            "status": "completed"
        }


        
        




