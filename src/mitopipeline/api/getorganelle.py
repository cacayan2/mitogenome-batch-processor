"""getorganelle.py

This module contains the API for running GetOrganelle on sequencing reads. 
"""

# Imports
from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample
from mitopipeline.models.command_result import CommandResult
from pathlib import Path
from logging import Logger
import shutil
import os

# Constants
VALID_ORGANELLE_TYPES = {
            "animal_mt",
            "embplant_pt",
            "embplant_mt",
            "fungus_mt",
            "fungus_nr",
            "embplant_nr",
            "anonym",
        }

class GetOrganelleRunner(BaseTool):
    """
    Class for running GetOrganelle on sequencing reads.
    """
    def __init__(self,
                 working_dir: Path,
                 output_dir: Path,
                 sample: Sample,
                 organelle_type: str,
                 tool_options: dict | None = None,
                 threads: int = 4,
                 logger: Logger | None = None,
                 tool_name: str = "getorganelle",
                 ) -> None:
        
        """Initialize GetOrganelleRunner.

        Args:
            working_dir (Path): The working directory for the tool.
            output_dir (Path): The output directory for the tool.
            sample (Sample): The sample object.
            logger (Logger | None, optional): The logger to use. Defaults to None.
            tool_name (str, optional): The name of the tool. Defaults to "getorganelle".

        Returns:
            None
        """
        super().__init__(tool_name=tool_name, working_dir=working_dir, logger=logger)
        self.sample = sample
        self.output_dir = output_dir
        self.threads = threads
        self.organelle_type = organelle_type
        self.tool_options = tool_options or {}

    def normalize_outputs(self) -> None:
        """Copy GetOrganelle outputs to standardized mitopipeline output names."""

        # Obtaining fasta and gfa candidates. 
        fasta_candidates = list(self.output_dir.glob("*.path_sequence.fasta"))
        gfa_candidates = list(self.output_dir.glob("*.selected_graph.gfa"))

        # Validating candidate files. 
        if not fasta_candidates:
            raise FileNotFoundError("No GetOrganelle path_sequence FASTA output found.")

        if not gfa_candidates:
            raise FileNotFoundError("No GetOrganelle selected_graph GFA output found.")

        # Creating fasta outputs and gfa outputs.
        fasta_output = self.output_dir / f"{self.sample.sample_id}.fasta"
        gfa_output = self.output_dir / f"{self.sample.sample_id}.gfa"

        # Copying outputs.
        shutil.copy2(fasta_candidates[0], fasta_output)
        shutil.copy2(gfa_candidates[0], gfa_output)

    def validate_inputs(self):
        """Validate inputs for the GetOrganelleRunner.

        Raises value errors if inputs are invalid and send to the logger.

        Returns:
            None
        """

        if self.organelle_type not in VALID_ORGANELLE_TYPES:
            raise ValueError(f"({self.tool_name}) Invalid organelle type {self.organelle_type}.")
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

    def build_command(self):
        """Build the command for GetOrganelleRunner.

        Returns:
            CommandResult: The command result object.
        """
        self.output_dir.mkdir(parents = True, exist_ok = True)
        command = ["get_organelle_from_reads.py",
                   "-1", str(self.sample.r1),
                   "-2", str(self.sample.r2),
                   "-o", str(self.output_dir),
                   "-F", self.organelle_type,
                   "-t", str(self.threads),
        ]

        return self._add_additional_getorganelle_args(command)

    def validate_outputs(self) -> None:
        """Validate and normalize GetOrganelle outputs.

        GetOrganelle produces output filenames based on organelle type, k-mer size,
        graph number, and result status. The pipeline standardizes those outputs
        to sample-specific filenames expected by Snakemake.

        Returns:
            None
        """
        outputs = self._expected_getorganelle_outputs()

        for output in outputs:
            if not output.exists():
                if self.logger is not None:
                    self.logger.error(
                        f"({self.tool_name}) Expected output file {output} does not exist."
                    )
                raise FileNotFoundError(
                    f"({self.tool_name}) Expected output file {output} does not exist."
                )


    def _normalize_getorganelle_outputs(self) -> None:
        """Copy GetOrganelle outputs to standardized mitopipeline output names."""

        fasta_candidates = sorted(self.output_dir.glob("*.path_sequence.fasta"))
        gfa_candidates = sorted(self.output_dir.glob("*.selected_graph.gfa"))

        if len(fasta_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one GetOrganelle path_sequence FASTA "
                f"in {self.output_dir}, found {len(fasta_candidates)}: {fasta_candidates}"
            )

        if len(gfa_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one GetOrganelle selected_graph GFA "
                f"in {self.output_dir}, found {len(gfa_candidates)}: {gfa_candidates}"
            )

        standardized_fasta = self.output_dir / f"{self.sample.sample_id}.fasta"
        standardized_gfa = self.output_dir / f"{self.sample.sample_id}.gfa"

        shutil.copy2(fasta_candidates[0], standardized_fasta)
        shutil.copy2(gfa_candidates[0], standardized_gfa)

        if self.logger is not None:
            self.logger.info(
                f"({self.tool_name}) Normalized FASTA output: "
                f"{fasta_candidates[0]} -> {standardized_fasta}"
            )
            self.logger.info(
                f"({self.tool_name}) Normalized GFA output: "
                f"{gfa_candidates[0]} -> {standardized_gfa}"
            )


    def _expected_getorganelle_outputs(self) -> list[Path]:
        """Return standardized mitopipeline output files for GetOrganelle.
        
        Returns: list[Path] A list of the expected outputs.
        """
        return [
            self.output_dir / f"{self.sample.sample_id}.fasta",
            self.output_dir / f"{self.sample.sample_id}.gfa",
        ]

    def _expected_getorganelle_outputs(self):
        """Returns the expected output files for GetOrganelleRunner.

        Returns:
            list[Path]: The expected output files for GetOrganelleRunner.
        """
        return [
            self.output_dir / f"{self.sample.sample_id}.fasta" ,
            self.output_dir / f"{self.sample.sample_id}.gfa"
        ]

    def _add_additional_getorganelle_args(self, command: list[str]) -> list[str]:
        """Add additional arguments to the GetOrganelleRunner command.

        Args:
            command (list[str]): The command to add arguments to.

        Returns:
            list[str]: The command with additional arguments.
        """
        # Creating dictionary of options for GetOrganelle.
        option_map = {
            "max_rounds": "-R",
            "kmer": "-k",
            "word_size": "-w",
            "pre_grouping": "-P",
            "max_reads": "--max-reads",
            "target_coverage": "--reduce-reads-for-coverage",
            "min_read_length": "--min-read-len",
            "max_read_length": "--max-read-len",
            "expected_max_size": "--expected-max-size",
            "expected_min_size": "--expected-min-size",
            "seed_file": "-s",
            "genes_file": "--genes",
            "exclude_fasta": "--exclude",
            "prefix": "--prefix",
            "round_output_prefix": "--out-per-round",
            "blast_path": "--which-blast",
            "bandage_path": "--which-bandage",
            "spades_path": "--which-spades",
        }

        # Iterating through options and adding them to the command.
        for option_name, flag in option_map.items():
            value = self.tool_options.get(option_name)

            if value is not None:
                command.extend([flag, str(value)])

        # Setting up boolean flags map.
        boolean_flag = {
            "overwrite": "--overwrite",
            "continue_run": "--continue",
            "fast_mode": "--fast",
            "disentangle": "--disentangle",
            "reverse_lsc": "--reverse-lsc",
            "no_slim": "--no-slim",
            "keep_temp_files": "--keep-temp-files",
            "verbose": "--verbose",
        }

        # Iterating through boolean flags and adding them to the command.
        for flag_name, flag in boolean_flag.items():
            if self.tool_options.get(flag_name, False):
                command.append(flag)

        return command
    
    def postprocess_outputs(self) -> None:
        """Postprocessing hook after running a successful command.

        Returns:
            None
        """
        self._normalize_getorganelle_outputs()