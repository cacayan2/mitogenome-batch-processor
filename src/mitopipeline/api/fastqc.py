"""fastqc.py

This module contains the API for running FastQC on raw sequencing reads.
"""

# Imports
from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample
from mitopipeline.models.command_result import CommandResult
from pathlib import Path
from logging import Logger

class FastQCRunner(BaseTool):
    """
    Class for running FastQC on raw sequencing reads.
    """
    def __init__(self,
                 working_dir: Path,
                 output_dir: Path,
                 sample: Sample,
                 logger: Logger | None = None,
                 tool_name: str = "fastqc",
                 threads: int = 4,
                 ):        
        """Initialize FastQCRunner.
        
        Args:
            working_dir (Path): The working directory for the tool.
            output_dir (Path): The output directory for the tool.
            sample (Sample): The sample object.
            logger (Logger | None, optional): The logger to use. Defaults to None.
            tool_name (str, optional): The name of the tool. Defaults to "fastqc"."""
        super().__init__(tool_name=tool_name, working_dir=working_dir, logger=logger)
        self.sample = sample
        self.output_dir = output_dir
        self.threads = threads

    def validate_inputs(self) -> None:
        """Validate inputs for the FastQCRunner. 
        
        Raises value errors if inputs are invalid and send to the logger.

        Returns:
            None
        """
        if not self.sample.r1.exists() or not self.sample.r1.is_file():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Input file {self.sample.r1} does not exist.")
            raise FileNotFoundError(f"({self.tool_name}) Input file {self.sample.r1} does not exist.")
        if not self.sample.r2.exists() or not self.sample.r2.is_file():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Input file {self.sample.r2} does not exist.")
            raise FileNotFoundError(f"({self.tool_name}) Input file {self.sample.r2} does not exist.")

    def build_command(self) -> list[str]:
        """Builds the command to run FastQC on raw sequencing reads. Also creates the output directory if not already created."""
        self.output_dir.mkdir(parents = True, exist_ok = True)
        return ["fastqc", 
                "--threads",
                str(self.threads),
                str(self.sample.r1), 
                str(self.sample.r2), 
                "-o", 
                str(self.output_dir),
                ]

    def validate_outputs(self) -> None:
        """Validate outputs for the FastQCRunner.
        
        Raises value errors if outputs are invalid and send to the logger.

        Returns:
            None
        """
        # Obtaining the expected output files.
        outputs = self._expected_fastqc_outputs()

        for expected_file in outputs:
            if not expected_file.exists():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output file {expected_file} does not exist.")
                raise FileNotFoundError(f"({self.tool_name}) Expected output file {expected_file} does not exist.")

    def run(self) -> CommandResult:
        """Runs the FastQCRunner and returns a CommandResult object.
        
        Returns:
            CommandResult: The result of running the FastQCRunner.
        """
        return super().run()

    def _expected_fastqc_outputs(self) -> list[Path]:
        """Returns the expected output files for FastQC.
        
        Returns:
            list[Path]: The expected output files for FastQC.
        """
        # Obtaining the stem of the input files.
        r1 = self._strip_fastq_suffix(self.sample.r1)
        r2 = self._strip_fastq_suffix(self.sample.r2)

        return [
            self.output_dir / f"{r1}_fastqc.html",
            self.output_dir / f"{r1}_fastqc.zip",
            self.output_dir / f"{r2}_fastqc.html",
            self.output_dir / f"{r2}_fastqc.zip"
        ]

    def _strip_fastq_suffix(self, fastq: Path) -> str:
        """Returns the FASTQ filename without FASTQ extensions.
        
        Args:
            fastq (Path): The path to the FASTQ file.
        
        Returns:
            str: The filename without the FASTQ extension.
        """
        # Obtaining the name of the FASTQ file.
        name = fastq.name

        # Removing each of the FASTQ extensions.
        if name.endswith(".fastq.gz"): return name[:-9]
        elif name.endswith(".fq.gz"): return name[:-6]
        elif name.endswith(".fastq"): return name[:-6]
        elif name.endswith(".fq"): return name[:-3]