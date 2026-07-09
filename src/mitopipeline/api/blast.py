"""BLAST API wrapper writing to one explicit output file."""

from __future__ import annotations

import os
import subprocess
from logging import Logger
from pathlib import Path

from mitopipeline.api.base_tool import BaseTool


VALID_BLAST_TASKS = {
    "blastn",
    "megablast",
    "dc-megablast",
    "blastn-short",
}

VALID_BLAST_MODES = {"local", "remote"}


class BlastRunner(BaseTool):
    """Run local or remote nucleotide BLAST."""

    def __init__(
        self,
        query_fasta: str | Path,
        database: str,
        output_file: str | Path,
        working_dir: str | Path,
        sample_id: str,
        mode: str = "local",
        threads: int = 4,
        task: str = "blastn",
        output_format: str = "6",
        evalue: float = 1e-5,
        max_target_seqs: int = 50,
        max_hsps: int | None = 1,
        perc_identity: float | None = None,
        query_coverage: float | None = None,
        word_size: int | None = None,
        logger: Logger | None = None,
    ) -> None:
        super().__init__(
            tool_name="blast",
            working_dir=Path(working_dir),
            logger=logger,
        )
        self.query_fasta = Path(query_fasta)
        self.database = database
        self.output_file = Path(output_file)
        self.sample_id = sample_id
        self.mode = mode
        self.threads = int(threads)
        self.task = task
        self.output_format = output_format
        self.evalue = evalue
        self.max_target_seqs = max_target_seqs
        self.max_hsps = max_hsps
        self.perc_identity = perc_identity
        self.query_coverage = query_coverage
        self.word_size = word_size

    def validate_inputs(self) -> None:
        if not self.query_fasta.is_file():
            raise FileNotFoundError(
                f"Query FASTA not found: {self.query_fasta}"
            )

        if self.mode not in VALID_BLAST_MODES:
            raise ValueError(f"Unsupported BLAST mode: {self.mode}")

        if self.task not in VALID_BLAST_TASKS:
            raise ValueError(f"Unsupported BLAST task: {self.task}")

        if self.mode == "local":
            result = subprocess.run(
                [
                    "blastdbcmd",
                    "-db",
                    self.database,
                    "-dbtype",
                    "nucl",
                    "-info",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise FileNotFoundError(
                    f"Invalid BLAST database: {self.database}. "
                    f"{result.stderr.strip()}"
                )

        if self.threads <= 0:
            raise ValueError("threads must be greater than zero.")

        cpus = os.cpu_count()
        if cpus is not None and self.threads > cpus:
            raise ValueError(
                f"threads exceed available CPUs: {self.threads} > {cpus}"
            )

    def build_command(self) -> list[str]:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "blastn",
            "-query",
            str(self.query_fasta),
            "-db",
            self.database,
            "-out",
            str(self.output_file),
            "-outfmt",
            self.output_format,
            "-task",
            self.task,
            "-evalue",
            str(self.evalue),
            "-max_target_seqs",
            str(self.max_target_seqs),
        ]

        if self.mode == "remote":
            command.append("-remote")
        else:
            command.extend(["-num_threads", str(self.threads)])

        if self.max_hsps is not None:
            command.extend(["-max_hsps", str(self.max_hsps)])

        if self.perc_identity is not None:
            command.extend(
                ["-perc_identity", str(self.perc_identity)]
            )

        if self.query_coverage is not None:
            command.extend(
                ["-qcov_hsp_perc", str(self.query_coverage)]
            )

        if self.word_size is not None:
            command.extend(["-word_size", str(self.word_size)])

        return command

    def validate_outputs(self) -> None:
        if not self.output_file.is_file():
            raise FileNotFoundError(
                f"BLAST output not found: {self.output_file}"
            )
