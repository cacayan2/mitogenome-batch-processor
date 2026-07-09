"""GetOrganelle API wrapper using one sample directory."""

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
    """Run GetOrganelle for one sample directory."""

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
    ) -> None:
        super().__init__(
            tool_name=tool_name,
            working_dir=Path(working_dir),
            logger=logger,
        )
        self.output_dir = Path(output_dir)
        self.sample = sample
        self.organelle_type = organelle_type
        self.tool_options = tool_options or {}
        self.threads = int(threads)

    @property
    def standardized_fasta(self) -> Path:
        return self.output_dir / "data.fasta"

    @property
    def standardized_gfa(self) -> Path:
        return self.output_dir / "graph.gfa"

    def validate_inputs(self) -> None:
        if self.organelle_type not in VALID_ORGANELLE_TYPES:
            raise ValueError(
                f"Unsupported organelle type: {self.organelle_type}"
            )

        for path in (self.sample.r1, self.sample.r2):
            if not path.is_file():
                raise FileNotFoundError(f"Input file not found: {path}")

        if self.threads <= 0:
            raise ValueError("threads must be greater than zero.")

        cpus = os.cpu_count()
        if cpus is not None and self.threads > cpus:
            raise ValueError(
                f"threads exceed available CPUs: {self.threads} > {cpus}"
            )

    def build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

        return self._add_options(command)

    def postprocess_outputs(self) -> None:
        fasta_candidates = sorted(
            self.output_dir.glob("*.path_sequence.fasta")
        )
        gfa_candidates = sorted(
            self.output_dir.glob("*.selected_graph.gfa")
        )

        if len(fasta_candidates) != 1:
            raise RuntimeError(
                "Expected exactly one GetOrganelle path_sequence FASTA "
                f"in {self.output_dir}; found {len(fasta_candidates)}."
            )

        if len(gfa_candidates) != 1:
            raise RuntimeError(
                "Expected exactly one GetOrganelle selected_graph GFA "
                f"in {self.output_dir}; found {len(gfa_candidates)}."
            )

        shutil.copy2(fasta_candidates[0], self.standardized_fasta)
        shutil.copy2(gfa_candidates[0], self.standardized_gfa)

        retained_names = {
            self.standardized_fasta.name,
            self.standardized_gfa.name,
            "assembly.log",
        }

        for child in self.output_dir.iterdir():
            if child.name in retained_names:
                continue

            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    def validate_outputs(self) -> None:
        for path in (self.standardized_fasta, self.standardized_gfa):
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError(
                    f"Missing or empty assembly output: {path}"
                )

    def _add_options(self, command: list[str]) -> list[str]:
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

        for key, flag in value_options.items():
            value = self.tool_options.get(key)
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

        for key, flag in boolean_options.items():
            if self.tool_options.get(key, False):
                command.append(flag)

        return command
