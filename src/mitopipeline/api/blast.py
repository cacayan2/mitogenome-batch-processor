"""blast.py

API wrapper for local and remote nucleotide BLAST searches.
"""

# Imports
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

VALID_BLAST_MODES = {
    "local",
    "remote",
}

DEFAULT_OUTFMT = (
    "6 qseqid sseqid pident length mismatch gapopen "
    "qstart qend sstart send evalue bitscore qcovs "
    "staxids sscinames stitle"
)


class BlastRunner(BaseTool):
    """Run local or NCBI remote nucleotide BLAST."""

    def __init__(
        self,
        query_fasta: str | Path,
        database: str,
        output_dir: str | Path,
        working_dir: str | Path,
        sample_id: str,
        mode: str = "local",
        threads: int = 4,
        task: str = "blastn",
        output_format: str = DEFAULT_OUTFMT,
        evalue: float = 1e-5,
        max_target_seqs: int = 50,
        max_hsps: int | None = 1,
        perc_identity: float | None = None,
        query_coverage: float | None = None,
        word_size: int | None = None,
        logger: Logger | None = None,
    ) -> None:
        """Initialize BLAST runner."""
        super().__init__(
            tool_name="blast",
            working_dir=Path(working_dir),
            logger=logger,
        )

        self.query_fasta = Path(query_fasta)
        self.database = database
        self.output_dir = Path(output_dir)
        self.sample_id = sample_id
        self.mode = mode
        self.threads = threads
        self.task = task
        self.output_format = output_format
        self.evalue = evalue
        self.max_target_seqs = max_target_seqs
        self.max_hsps = max_hsps
        self.perc_identity = perc_identity
        self.query_coverage = query_coverage
        self.word_size = word_size

    def validate_inputs(self) -> None:
        """Validate query, database, and BLAST options."""
        if not self.query_fasta.exists():
            raise FileNotFoundError(
                f"({self.tool_name}) Query FASTA does not exist: "
                f"{self.query_fasta}"
            )

        if not self.query_fasta.is_file():
            raise ValueError(
                f"({self.tool_name}) Query FASTA is not a file: "
                f"{self.query_fasta}"
            )

        if self.query_fasta.stat().st_size == 0:
            raise ValueError(
                f"({self.tool_name}) Query FASTA is empty: "
                f"{self.query_fasta}"
            )

        if self.mode not in VALID_BLAST_MODES:
            raise ValueError(
                f"({self.tool_name}) Unsupported BLAST mode: "
                f"{self.mode}"
            )

        if not self.database.strip():
            raise ValueError(
                f"({self.tool_name}) database must not be empty."
            )

        if not self.sample_id.strip():
            raise ValueError(
                f"({self.tool_name}) sample_id must not be empty."
            )

        if self.mode == "local":
            self._validate_local_database()

        available_cpus = os.cpu_count()

        if self.threads <= 0:
            raise ValueError(
                f"({self.tool_name}) threads must be greater than zero."
            )

        if (
            available_cpus is not None
            and self.threads > available_cpus
        ):
            raise ValueError(
                f"({self.tool_name}) Threads exceed available CPUs: "
                f"{self.threads} > {available_cpus}"
            )

        if self.task not in VALID_BLAST_TASKS:
            raise ValueError(
                f"({self.tool_name}) Unsupported BLAST task: "
                f"{self.task}"
            )

        if self.evalue <= 0:
            raise ValueError(
                f"({self.tool_name}) evalue must be greater than zero."
            )

        if self.max_target_seqs <= 0:
            raise ValueError(
                f"({self.tool_name}) max_target_seqs must be "
                f"greater than zero."
            )

        if self.max_hsps is not None and self.max_hsps <= 0:
            raise ValueError(
                f"({self.tool_name}) max_hsps must be greater than zero."
            )

        if (
            self.perc_identity is not None
            and not 0 <= self.perc_identity <= 100
        ):
            raise ValueError(
                f"({self.tool_name}) perc_identity must be "
                f"between 0 and 100."
            )

        if (
            self.query_coverage is not None
            and not 0 <= self.query_coverage <= 100
        ):
            raise ValueError(
                f"({self.tool_name}) query_coverage must be "
                f"between 0 and 100."
            )

        if self.word_size is not None and self.word_size <= 0:
            raise ValueError(
                f"({self.tool_name}) word_size must be greater than zero."
            )

    def build_command(self) -> list[str]:
        """Build blastn command."""
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            "blastn",
            "-query",
            str(self.query_fasta),
            "-db",
            self.database,
            "-out",
            str(self._expected_blast_output()),
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
            command.extend([
                "-num_threads",
                str(self.threads),
            ])

        if self.max_hsps is not None:
            command.extend([
                "-max_hsps",
                str(self.max_hsps),
            ])

        if self.perc_identity is not None:
            command.extend([
                "-perc_identity",
                str(self.perc_identity),
            ])

        if self.query_coverage is not None:
            command.extend([
                "-qcov_hsp_perc",
                str(self.query_coverage),
            ])

        if self.word_size is not None:
            command.extend([
                "-word_size",
                str(self.word_size),
            ])

        return command

    def validate_outputs(self) -> None:
        """Validate BLAST output."""
        output_file = self._expected_blast_output()

        if not output_file.exists():
            raise FileNotFoundError(
                f"({self.tool_name}) Expected output does not exist: "
                f"{output_file}"
            )

        if not output_file.is_file():
            raise ValueError(
                f"({self.tool_name}) Expected output is not a file: "
                f"{output_file}"
            )

        if (
            output_file.stat().st_size == 0
            and self.logger is not None
        ):
            self.logger.warning(
                f"({self.tool_name}) BLAST returned no hits for "
                f"sample {self.sample_id}."
            )

    def _validate_local_database(self) -> None:
        """Validate local database through blastdbcmd."""
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
                f"({self.tool_name}) Local BLAST database is missing "
                f"or invalid: {self.database}. "
                f"{result.stderr.strip()}"
            )

    def _expected_blast_output(self) -> Path:
        """Return expected BLAST output path."""
        return (
            self.output_dir
            / f"{self.sample_id}.blast.tsv"
        )