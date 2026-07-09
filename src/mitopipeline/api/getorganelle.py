"""getorganelle.py

API wrapper for running GetOrganelle on sequencing reads.

GetOrganelle writes many native output files. To support parallel sample
execution, each sample should run in its own tool output directory, e.g.:

    outputs/<job_id>/assembly/work/<sample_id>/

The normalized pipeline outputs are copied to:

    outputs/<job_id>/assembly/<sample_id>.fasta
    outputs/<job_id>/assembly/<sample_id>.gfa
"""

from __future__ import annotations

from logging import Logger
import os
from pathlib import Path
import shutil

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample


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
    """Run GetOrganelle for one sample."""

    def __init__(
            self,
            working_dir: Path,
            output_dir: Path,
            sample: Sample,
            organelle_type: str,
            tool_options: dict | None = None,
            threads: int = 4,
            logger: Logger | None = None,
            tool_name: str = "getorganelle",
            final_output_dir: Path | None = None,
    ) -> None:
        """Initialize GetOrganelleRunner.

        Args:
            working_dir: Working directory for command execution.
            output_dir: Sample-specific GetOrganelle native output directory.
            sample: Sample object.
            organelle_type: GetOrganelle database type.
            tool_options: Optional GetOrganelle CLI options.
            threads: Number of threads.
            logger: Optional logger.
            tool_name: Name used for logging.
            final_output_dir: Directory for normalized pipeline outputs.
        """
        super().__init__(
            tool_name=tool_name,
            working_dir=working_dir,
            logger=logger,
        )

        self.sample = sample
        self.output_dir = Path(output_dir)
        self.final_output_dir = (
            Path(final_output_dir)
            if final_output_dir is not None
            else self.output_dir
        )
        self.threads = threads
        self.organelle_type = organelle_type
        self.tool_options = tool_options or {}

    @property
    def standardized_fasta(self) -> Path:
        """Return normalized FASTA output path."""
        return self.final_output_dir / f"{self.sample.sample_id}.fasta"

    @property
    def standardized_gfa(self) -> Path:
        """Return normalized GFA output path."""
        return self.final_output_dir / f"{self.sample.sample_id}.gfa"

    def validate_inputs(self) -> None:
        """Validate GetOrganelle inputs."""
        if self.organelle_type not in VALID_ORGANELLE_TYPES:
            raise ValueError(
                f"({self.tool_name}) Invalid organelle type "
                f"{self.organelle_type}."
            )

        if not self.sample.r1.exists() or not self.sample.r1.is_file():
            raise FileNotFoundError(
                f"({self.tool_name}) Input file {self.sample.r1} "
                "does not exist."
            )

        if not self.sample.r2.exists() or not self.sample.r2.is_file():
            raise FileNotFoundError(
                f"({self.tool_name}) Input file {self.sample.r2} "
                "does not exist."
            )

        if self.threads <= 0:
            raise ValueError(
                f"({self.tool_name}) Invalid number of threads "
                f"{self.threads}."
            )

        available_cpus = os.cpu_count()

        if available_cpus is not None and self.threads > available_cpus:
            raise ValueError(
                f"({self.tool_name}) Number of threads exceeds available "
                f"cores. {self.threads} > {available_cpus}."
            )

    def build_command(self) -> list[str]:
        """Build the GetOrganelle command."""
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            "get_organelle_from_reads.py",
            "-1",
            str(self.sample.r1),
            "-2",
            str(self.sample.r2),
            "-o",
            str(self.output_dir),
            "-F",
            self.organelle_type,
            "-t",
            str(self.threads),
        ]

        return self._add_additional_getorganelle_args(
            command
        )

    def validate_outputs(self) -> None:
        """Validate normalized pipeline outputs."""
        for output in self._expected_getorganelle_outputs():
            if not output.exists():
                raise FileNotFoundError(
                    f"({self.tool_name}) Expected output file "
                    f"{output} does not exist."
                )

    def _normalize_getorganelle_outputs(self) -> None:
        """Copy GetOrganelle native outputs to normalized pipeline names."""
        fasta_candidates = sorted(
            self.output_dir.glob("*.path_sequence.fasta")
        )
        gfa_candidates = sorted(
            self.output_dir.glob("*.selected_graph.gfa")
        )

        if len(fasta_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one GetOrganelle "
                f"path_sequence FASTA in {self.output_dir}, found "
                f"{len(fasta_candidates)}: {fasta_candidates}"
            )

        if len(gfa_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one GetOrganelle "
                f"selected_graph GFA in {self.output_dir}, found "
                f"{len(gfa_candidates)}: {gfa_candidates}"
            )

        self.final_output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        fasta_source = fasta_candidates[0]
        gfa_source = gfa_candidates[0]

        shutil.copy2(
            fasta_source,
            self.standardized_fasta,
        )
        shutil.copy2(
            gfa_source,
            self.standardized_gfa,
        )

        if self.logger is not None:
            self.logger.info(
                f"({self.tool_name}) Normalized FASTA output: "
                f"{fasta_source} -> {self.standardized_fasta}"
            )
            self.logger.info(
                f"({self.tool_name}) Normalized GFA output: "
                f"{gfa_source} -> {self.standardized_gfa}"
            )

    def _expected_getorganelle_outputs(self) -> list[Path]:
        """Return expected normalized pipeline outputs."""
        return [
            self.standardized_fasta,
            self.standardized_gfa,
        ]

    def _add_additional_getorganelle_args(
            self,
            command: list[str],
    ) -> list[str]:
        """Add optional GetOrganelle arguments."""
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
            "disentangle_df": "--disentangle-df",
            "disentangle_time_limit": "--disentangle-time-limit",
        }

        for option_name, flag in option_map.items():
            value = self.tool_options.get(option_name)

            if value is not None:
                command.extend(
                    [
                        flag,
                        str(value),
                    ]
                )

        boolean_flags = {
            "overwrite": "--overwrite",
            "continue_run": "--continue",
            "fast_mode": "--fast",
            "reverse_lsc": "--reverse-lsc",
            "no_slim": "--no-slim",
            "keep_temp_files": "--keep-temp-files",
            "verbose": "--verbose",
        }

        for flag_name, flag in boolean_flags.items():
            if self.tool_options.get(flag_name, False):
                command.append(flag)

        return command

    def postprocess_outputs(self) -> None:
        """Normalize GetOrganelle outputs after successful execution."""
        self._normalize_getorganelle_outputs()