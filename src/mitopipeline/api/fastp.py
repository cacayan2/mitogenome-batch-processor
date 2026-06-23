"""fastp.py

This module contains the API for running fastp on raw sequencing reads.
"""

# Imports
from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample
from mitopipeline.models.command_result import CommandResult
from pathlib import Path
from logging import Logger
import os

class FastpRunner(BaseTool):
    """
    Class for running fastp on raw sequencing reads.
    """

    def __init__(self,
                 working_dir: Path,
                 output_dir: Path,
                 sample: Sample,
                 tool_options: dict | None = None,
                 threads: int = 4,
                 logger: Logger | None = None,
                 tool_name: str = "fastp",
                 ):
        """Initialize FastPRunner.
        
        Args:
            working_dir (Path): The working directory for the tool.
            output_dir (Path): The output directory for the tool.
            sample (Sample): The sample object.
            logger (Logger | None, optional): The logger to use. Defaults to None.
            tool_name (str, optional): The name of the tool. Defaults to "fastp".
        """
        super().__init__(tool_name=tool_name, working_dir=working_dir, logger=logger)
        self.sample = sample
        self.output_dir = output_dir
        self.threads = threads
        self.tool_options = tool_options or {}

        
    def validate_inputs(self) -> None:
        """Validate inputs for the FastPRunner.
        
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
        if not self.threads > 0:
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Invalid number of threads {self.threads}.")
            raise ValueError(f"({self.tool_name}) Invalid number of threads {self.threads}.")
        if not self.threads <= os.cpu_count():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Number of threads exceeds available cores. {self.threads} > {os.cpu_count()}.")
            raise ValueError(f"({self.tool_name}) Number of threads exceeds available cores. {self.threads} > {os.cpu_count()}.")

    def build_command(self) -> list[str]:
        """Build the command for running fastp on raw sequencing reads. Also creates the output directory if not already created."""
        self.output_dir.mkdir(parents = True, exist_ok = True)
        command = ["fastp",
                "--in1", str(self.sample.r1),
                "--in2", str(self.sample.r2),
                "--out1", str(self.output_dir / f"{self.sample.sample_id}_R1.trimmed.fastq.gz"),
                "--out2", str(self.output_dir / f"{self.sample.sample_id}_R2.trimmed.fastq.gz"),
                "--html", str(self.output_dir / f"{self.sample.sample_id}.fastp.html"),
                "--json", str(self.output_dir / f"{self.sample.sample_id}.fastp.json"),
                "--thread", str(self.threads),
        ]

        return self._add_additional_fastp_args(command)
    
    def validate_outputs(self) -> None:
        """Validate outputs for the FastPRunner.

        Raises value errors if outputs are invalid and send to the logger.

        Returns:
            None
        """
        # Obtaining the expected output files.
        outputs = self._expected_fastp_outputs()

        for expected_file in outputs:
            if not expected_file.exists():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output file {expected_file} does not exist.")
                raise FileNotFoundError(f"({self.tool_name}) Expected output file {expected_file} does not exist.")

    def run(self) -> CommandResult:
        """Runs the FastPRunner and returns a CommandResult object.

        Returns:
            CommandResult: The result of running the FastPRunner.
        """
        return super().run()

    def _expected_fastp_outputs(self) -> list[Path]:
        """Returns the expected output files for fastp.
        
        Returns:
            list[Path]: The expected output files for fastp.
        """
        # Obtaining thae stem of the input files.
        r1 = self._strip_fastq_suffix(self.sample.r1)
        r2 = self._strip_fastq_suffix(self.sample.r2)

        return [
            self.output_dir / f"{r1}.trimmed.fastq.gz",
            self.output_dir / f"{r2}.trimmed.fastq.gz",
            self.output_dir / f"{self.sample.sample_id}.fastp.html",
            self.output_dir / f"{self.sample.sample_id}.fastp.json",
        ]

    def _strip_fastq_suffix(self, fastq: Path) -> str:
        """Strips the suffix of a fastq file path.
        
        Args:
            fastq_path (Path): The fastq file path.
        
        Returns:
            str: The stem of the fastq file path.
        """
        # Obtaining the name of the FASTQ file.
        name = fastq.name

        # Removing each of the FASTQ extensions.
        if name.endswith(".fastq.gz"): return name[:-9]
        elif name.endswith(".fq.gz"): return name[:-6]
        elif name.endswith(".fastq"): return name[:-6]
        elif name.endswith(".fq"): return name[:-3]

    def _add_additional_fastp_args(self, command: list[str]) -> list[str]:
        """Add additional arguments to the fastp command.
        
        Args:
            command (list[str]): The fastp command.
        
        Returns:
            list[str]: The fastp command with additional arguments.
        """
        # Creating dictionary of options for fastp.
        option_map = {
            "qualified_quality_phred": "--qualified_quality_phred",
            "length_required": "--length_required",
            "trim_front1": "--trim_front1",
            "trim_tail1": "--trim_tail1",
        }

        # Iterating through options and adding them to the command.
        for option_name, flag in option_map.items():
            value = self.tool_options.get(option_name)

            if value is not None:
                command.extend([flag, str(value)])
        
        # Setting up boolean flags map. 
        boolean_flag = {
            "cut_front": "--cut_front",
            "cut_tail": "--cut_tail",
            "cut_right": "--cut_right",
            "detect_adapter_for_pe": "--detect_adapter_for_pe", 
        }

        # Iterating through boolean options and adding them to the command.
        for option_name, flag in boolean_flag.items():
            if self.tool_options.get(option_name):
                command.append(flag)

        return command