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
from dataclasses import field
class PipelineJob():
    """Manages the lifecycle and job metadata for a pipeline run.

    This class handles the creation of a job directory, logging, and job metadata. 
    It generates a unique job ID if one is not provided, and creates a logger for the job.
    """
    def __init__(self, parent_dir: Path, job_id: str = None, samples: list[str] = field(default_factory = list)):
        """Initializes a PipelineRun object.

        Creates a unique job ID if one is not provided, and creates a logger for the job. 
        Creates a job directory in the specified parent directory.

        Args:
            parent_dir (Path): The parent directory for the job directory.
            job_id (str, optional): The job ID. Defaults to None and will be generated if not provided. 
            samples (list[str], optional): A list of sample names. Defaults to an empty list.
        """
        # Setting default value for is a new job to True - this will change in subsequent logic structures. 
        self.is_new_job = True
        
        # Verifying if the job exists. Pipeline will either progress where last job left off or start a new job.
        if job_id is not None:
            self.is_new_job = False
            self.job_id = job_id
        # Else branch assigns a new job ID for the job.
        else:
            now = datetime.now()
            self.job_id = f"{now.strftime("%Y%m%d")}_{now.strftime("%H%M")}_{str(uuid.uuid4())}"

        # Instantiation of member variables. 
        self.start_time = datetime.now()
        self.end_time = None
        self.created_time = None
        self.failed_time = None
        self.runtime = None
        self.parent_dir = parent_dir
        self.job_dir = self.parent_dir / self.job_id
        self.samples = samples
        self.job_logger = self.create_output_directory()
        self.job_logger.info(f"({self.job_id}) Pipeline job {self.job_id} started at {self.start_time}.") 
        
        # Marks the job as created.
        self.mark_created()

    def create_output_directory(self) -> logging.Logger:
        """Upon instantiation of a PipelineJob object, this method will create a job directory in the specified parent directory.

        Returns:
            logging.Logger: A logger for the job.
        """
        # Parent directory must exist - if it doesn't raise an error (job object is not created).
        if not self.parent_dir.exists():
            raise FileNotFoundError(f"Failed to find parent directory specified: {self.parent_dir}, stopping pipeline execution.")
        if not self.job_dir.exists():
            # Makes the new job directory if it doesn't exist.
            self.job_dir.mkdir(parents = True, exist_ok = True)
            
            # List of subdirectories to be created. 
            dirs = [
                self.job_dir / "logs",
                self.job_dir / "qc_raw",
                self.job_dir / "qc_trimmed",
                self.job_dir / "trimming",
                self.job_dir / "assembly",
                self.job_dir / "annotation",
                self.job_dir / "phylogeny",
                self.job_dir / "reports",
                self.job_dir / "stats",
                self.job_dir / "submission"
            ]
            
            # Iterate through list of subdirectories and create it. 
            for dir in dirs:
                if not dir.exists():
                    dir.mkdir(parents = True, exist_ok = True)
    
            # Creates a logger for the job, assigns a path to the logger.
            job_logger = make_logger(name = self.job_id, log_file_path = self.job_dir / "logs" / f"pipeline_job.log")

            # Returns the job logger. 
            return job_logger
    
    def mark_created(self):
            """Marks the pipeline job as created and records associated metadata."""
            self.created_time = datetime.now()
            self.runtime = self.created_time - self.start_time
            
            data = {
                "job_id": self.job_id,
                "start_time": self.start_time.isoformat(),
                "event_time": self.created_time.isoformat(),
                "runtime_seconds": self.runtime.total_seconds(),
                "output_dir": str(self.job_dir),
                "sample_count": len(self.samples),
                "samples": self.samples,
                "status": "created"
            }
            
            # Log status
            if self.is_new_job:
                self.job_logger.info(f"({self.job_id}) Pipeline job {self.job_id} is a new job, new directory was successfully created at {self.job_dir}.")
            else:
                self.job_logger.info(f"({self.job_id}) Pipeline job {self.job_id} already exists, using existing directory and automatically progressing pipeline from previous run ({self.job_dir}).")
                
            # Write live and append history
            self.write_metadata(data)

    def mark_completed(self):
        """Marks the pipeline job as completed and records associated metadata."""
        self.end_time = datetime.now()
        self.runtime = self.end_time - self.start_time
        
        data = {
            "job_id": self.job_id,
            "start_time": self.start_time.isoformat(),
            "event_time": self.end_time.isoformat(),
            "runtime_seconds": self.runtime.total_seconds(),
            "output_dir": str(self.job_dir),
            "sample_count": len(self.samples),
            "samples": self.samples,
            "status": "completed"
        }
        
        self.job_logger.info(f"({self.job_id}) Pipeline job {self.job_id} completed at {self.end_time}.")
        
        # Write live and append history
        self.write_metadata(data)

    def mark_failed(self):
        """Marks the pipeline job as failed and records associated metadata."""
        self.failed_time = datetime.now()
        self.runtime = self.failed_time - self.start_time
        
        data = {
            "job_id": self.job_id,
            "start_time": self.start_time.isoformat(),
            "event_time": self.failed_time.isoformat(),
            "runtime_seconds": self.runtime.total_seconds(),
            "output_dir": str(self.job_dir),
            "sample_count": len(self.samples),
            "samples": self.samples,
            "status": "failed"
        }
        
        self.job_logger.info(f"({self.job_id}) Pipeline job {self.job_id} failed at {self.failed_time}. Job details can be found in {self.job_dir}.")
        
        # Write live and append history
        self.write_metadata(data)

    def write_metadata(self, data: dict):
        """Helper method to centralize the dual-file writing logic."""
        live_file = self.job_dir / "job_metadata.json"
        history_file = self.job_dir / "job_events.json"

        # 1. Overwrite the live snapshot file
        with open(live_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # 2. Append to the audit history file
        if not history_file.exists():
            history_file.write_text("[]", encoding="utf-8")

        with open(history_file, "r+", encoding="utf-8") as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                history_data = [] # Fallback if file got corrupted
            
            history_data.append(data)
            
            # Reset file pointer to overwrite history with the updated array
            f.seek(0)
            json.dump(history_data, f, indent=4)
            f.truncate()

        self.job_logger.info(f"({self.job_id}) Wrote job metadata to {live_file} and {history_file}.")

            
            




