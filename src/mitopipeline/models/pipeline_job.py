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
        self._created_time = None
        self._failed_time = None
        self._runtime = None
        self._parent_dir = parent_dir
        self._job_dir = self._parent_dir / self._job_id
        self._samples = samples
        self._job_logger = self.__create_output_directory()
        self._job_logger.info(f"Pipeline job {self._job_id} started at {self._start_time}.") 
        
        # Marks the job as created.
        self.mark_created()

    def __create_output_directory(self) -> logging.Logger:
        """Upon instantiation of a PipelineJob object, this method will create a job directory in the specified parent directory.

        Returns:
            logging.Logger: A logger for the job.
        """
        # Parent directory must exist - if it doesn't raise an error (job object is not created).
        if not self._parent_dir.exists():
            raise FileNotFoundError(f"Failed to find parent directory specified: {self.parent_dir}, stopping pipeline execution.")
        if not self._job_dir.exists():
            # Makes the new job directory if it doesn't exist.
            self._job_dir.mkdir(parents = True, exist_ok = True)
            
            # List of subdirectories to be created. 
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
            
            # Iterate through list of subdirectories and create it. 
            for dir in dirs:
                if not dir.exists():
                    dir.mkdir(parents = True, exist_ok = True)
    
            # Creates a logger for the job, assigns a path to the logger.
            job_logger = make_logger(name = self._job_id, log_file_path = self._job_dir / "logs" / f"pipeline_job.log")

            # Returns the job logger. 
            return job_logger
    
    def mark_created(self):
            """Marks the pipeline job as created and records associated metadata."""
            self._created_time = datetime.now()
            self._runtime = self._created_time - self._start_time
            
            data = {
                "job_id": self._job_id,
                "start_time": self._start_time.isoformat(),
                "event_time": self._created_time.isoformat(),
                "runtime_seconds": self._runtime.total_seconds(),
                "output_dir": str(self._job_dir),
                "sample_count": len(self._samples),
                "samples": self._samples,
                "status": "created"
            }
            
            # Log status
            if self._is_new_job:
                self._job_logger.info(f"Pipeline job {self._job_id} is a new job, new directory was successfully created at {self._job_dir}.")
            else:
                self._job_logger.info(f"Pipeline job {self._job_id} already exists, using existing directory and automatically progressing pipeline from previous run ({self._job_dir}).")
                
            # Write live and append history
            self._write_metadata(data)

    def mark_completed(self):
        """Marks the pipeline job as completed and records associated metadata."""
        self._end_time = datetime.now()
        self._runtime = self._end_time - self._start_time
        
        data = {
            "job_id": self._job_id,
            "start_time": self._start_time.isoformat(),
            "event_time": self._end_time.isoformat(),
            "runtime_seconds": self._runtime.total_seconds(),
            "output_dir": str(self._job_dir),
            "sample_count": len(self._samples),
            "samples": self._samples,
            "status": "completed"
        }
        
        self._job_logger.info(f"Pipeline job {self._job_id} completed at {self._end_time}.")
        
        # Write live and append history
        self._write_metadata(data)

    def mark_failed(self):
        """Marks the pipeline job as failed and records associated metadata."""
        self._failed_time = datetime.now()
        self._runtime = self._failed_time - self._start_time
        
        data = {
            "job_id": self._job_id,
            "start_time": self._start_time.isoformat(),
            "event_time": self._failed_time.isoformat(),
            "runtime_seconds": self._runtime.total_seconds(),
            "output_dir": str(self._job_dir),
            "sample_count": len(self._samples),
            "samples": self._samples,
            "status": "failed"
        }
        
        self._job_logger.info(f"Pipeline job {self._job_id} failed at {self._failed_time}. Job details can be found in {self._job_dir}.")
        
        # Write live and append history
        self._write_metadata(data)

    def _write_metadata(self, data: dict):
        """Helper method to centralize the dual-file writing logic."""
        live_file = self._job_dir / "job_metadata.json"
        history_file = self._job_dir / "job_events.json"

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
    
    # Getters
    def get_job_id(self): return self._job_id
    def get_job_dir(self): return self._job_dir
    def get_samples(self): return self._samples
    def get_logger(self): return self._job_logger
    def get_start_time(self): return self._start_time
    def get_end_time(self): return self._end_time
    def get_runtime(self): return self._runtime
    def get_parent_dir(self): return self._parent_dir
    def get_is_new_job(self): return self._is_new_job

    # Setters
    def set_job_id(self, job_id): self._job_id = job_id
    def set_job_dir(self, job_dir): self._job_dir = job_dir
    def set_samples(self, samples): self._samples = samples
    def set_logger(self, logger): self._job_logger = logger
    def set_start_time(self, start_time): self._start_time = start_time
    def set_end_time(self, end_time): self._end_time = end_time
    def set_runtime(self, runtime): self._runtime = runtime
    def set_parent_dir(self, parent_dir): self._parent_dir = parent_dir
    def set_is_new_job(self, is_new_job): self._is_new_job = is_new_job

    # Deleters
    def del_job_id(self): del self._job_id
    def del_job_dir(self): del self._job_dir
    def del_samples(self): del self._samples
    def del_logger(self): del self._job_logger
    def del_start_time(self): del self._start_time
    def del_end_time(self): del self._end_time
    def del_runtime(self): del self._runtime
    def del_parent_dir(self): del self._parent_dir


            
            




