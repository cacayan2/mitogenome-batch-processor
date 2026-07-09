"""getorganelle.py

Parallel-safe API wrapper for GetOrganelle.
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
        final_output_dir: Path,
        sample: Sample,
        organelle_type: str,
        tool_options: dict | None = None,
        threads: int = 4,
        logger: Logger | None = None,
        tool_name: str = "getorganelle",
    ) -> None:
        super().__init__(
            tool_name=tool_name,
            working_dir=Path(working_dir),
            logger=logger,
        )
        self.sample = sample
        self.output_dir = Path(output_dir)
        self.final_output_dir = Path(final_output_dir)
        self.threads = threads
        self.organelle_type = organelle_type
        self.tool_options = tool_options or {}

    @property
    def standardized_fasta(self) -> Path:
        return self.final_output_dir / f"{self.sample.sample_id}.fasta"

    @property
    def standardized_gfa(self) -> Path:
        return self.final_output_dir / f"{self.sample.sample_id}.gfa"

    def validate_inputs(self) -> None:
        if self.organelle_type not in VALID_ORGANELLE_TYPES:
            raise ValueError(
                f"({self.tool_name}) Invalid organelle type "
                f"{self.organelle_type}."
            )

        for read_path in (self.sample.r1, self.sample.r2):
            if not read_path.exists() or not read_path.is_file():
                raise FileNotFoundError(
                    f"({self.tool_name}) Input file does not exist: "
                    f"{read_path}"
                )

        if self.threads <= 0:
            raise ValueError(
                f"({self.tool_name}) Invalid thread count: {self.threads}."
            )

        available_cpus = os.cpu_count()
        if available_cpus is not None and self.threads > available_cpus:
            raise ValueError(
                f"({self.tool_name}) Threads exceed available CPUs: "
                f"{self.threads} > {available_cpus}."
            )

    def build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.final_output_dir.mkdir(parents=True, exist_ok=True)

        if self.logger is not None:
            self.logger.debug(
                f"({self.tool_name}) Native output directory: "
                f"{self.output_dir}"
            )
            self.logger.debug(
                f"({self.tool_name}) Final output directory: "
                f"{self.final_output_dir}"
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

        return self._add_additional_getorganelle_args(command)

    def validate_outputs(self) -> None:
        for output in self._expected_getorganelle_outputs():
            if not output.exists():
                raise FileNotFoundError(
                    f"({self.tool_name}) Expected output does not exist: "
                    f"{output}"
                )
            if not output.is_file() or output.stat().st_size == 0:
                raise ValueError(
                    f"({self.tool_name}) Expected output is empty or invalid: "
                    f"{output}"
                )

    def postprocess_outputs(self) -> None:
        fasta_candidates = sorted(
            self.output_dir.glob("*.path_sequence.fasta")
        )
        gfa_candidates = sorted(
            self.output_dir.glob("*.selected_graph.gfa")
        )

        if self.logger is not None:
            self.logger.debug(
                f"({self.tool_name}) FASTA candidates: "
                f"{fasta_candidates}"
            )
            self.logger.debug(
                f"({self.tool_name}) GFA candidates: "
                f"{gfa_candidates}"
            )

        if len(fasta_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one path_sequence "
                f"FASTA in {self.output_dir}; found "
                f"{len(fasta_candidates)}."
            )

        if len(gfa_candidates) != 1:
            raise RuntimeError(
                f"({self.tool_name}) Expected exactly one selected_graph GFA "
                f"in {self.output_dir}; found {len(gfa_candidates)}."
            )

        shutil.copy2(fasta_candidates[0], self.standardized_fasta)
        shutil.copy2(gfa_candidates[0], self.standardized_gfa)

        if self.logger is not None:
            self.logger.info(
                f"({self.tool_name}) Wrote normalized FASTA: "
                f"{self.standardized_fasta}"
            )
            self.logger.info(
                f"({self.tool_name}) Wrote normalized GFA: "
                f"{self.standardized_gfa}"
            )

    def _expected_getorganelle_outputs(self) -> list[Path]:
        return [self.standardized_fasta, self.standardized_gfa]

    def _add_additional_getorganelle_args(
        self,
        command: list[str],
    ) -> list[str]:
        value_options = {
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

        for option_name, flag in value_options.items():
            value = self.tool_options.get(option_name)
            if value is not None:
                command.extend([flag, str(value)])

        boolean_options = {
            "overwrite": "--overwrite",
            "continue_run": "--continue",
            "fast_mode": "--fast",
            "reverse_lsc": "--reverse-lsc",
            "no_slim": "--no-slim",
            "keep_temp_files": "--keep-temp-files",
            "verbose": "--verbose",
        }

        for option_name, flag in boolean_options.items():
            if self.tool_options.get(option_name, False):
                command.append(flag)

        return command
