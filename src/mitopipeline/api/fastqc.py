"""
fastqc.py

FastQC wrapper which supports parallelization using a single sample directory.
"""

# Imports
from __future__ import annotations
from logging import Logger
from pathlib import Path
import shutil
import os
from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample

class FastQCRunner(BaseTool):
    """
    This class provides the functionality to run FastQC and normalize I/O 
    within a single sample directory. 
    """
    
    def __init__(self,
                 working_dir: Path,
                 output_dir: Path,
                 sample: Sample,
                 r1_output_stem: str,
                 r2_output_stem: str,
                 logger: Logger | None = None, 
                 tool_name: str = "fastqc",
                 threads: int = 4) -> None:
        """
        Instantiation method for the creation of the 
        FastQC Runner class. Calls the BaseTool instantiation methods and
        sets a few other object variables.

        Args:
            working_dir (Path): The path to the directory of the input files.
            output_dir (Path): The directory to save the output files to.
            sample (Sample): The sample object that is being worked with.
            r1_output_stem (str): The stem of the R1 file - this will be appended to with file extensions for the outputs.
            r2_output_stem (str): The stem of the R2 file - this will be appended to with file extensions for the outputs.
            logger (Logger): The logger to use for this of the pipeline.
            tool_name (str): The name of the tool (by default will be fastqc).
            threads (int): The number of the threads for this process to use.
        Returns: 
            None
        """
        # FastQCRunner inherits from BaseTool - here we invoke BaseTool's
        # instantiation function within FastQCRunner's instantiation function. 
        super().__init__(
            tool_name = tool_name,
            workind_dir = Path(working_dir),
            logger = logger
        )        
        
        # Setting the other class variables.
        self.output_dir = Path(output_dir)
        self.sample = sample
        self.r1_output_stem = r1_output_stem
        self.r2_output_stem = r2_output_stem
        self.threads = int(threads)
        
    def validate_inputs(self) -> None:
        """
        Validates the input R1 and R2 files for FastQC.
        This function appropriately logs the result,
        raises an error otherwise. 
        """
        for path in (self.sample.r1, self.sample.r2):
            if not path.is_file():
                if self.logger is not None: self.logger.error(f"Input file not found: {path}.")
                raise FileNotFoundError(f"[{self.tool_name}] Input file not found: {path}.")
        
        if self.threads <= 0:
            if self.logger is not None: self.logger.error(f"Threads must be greater than 0 (passed value: {self.threads}).")
            raise ValueError(f"[{self.tool_name}] Threads must be greater than 0 (passed value: {self.threads}).")
        
        if self.threads > os.cpu_count():
            if self.logger is not None: self.logger.warn(f"Number of threads passed exceeds the number ")