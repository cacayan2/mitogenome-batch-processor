"""blast.py

API wrapper for running local nucleotide BLAST searches.
"""

# Imports
import os
from logging import Logger
from pathlib import Path

from mitopipeline.api.base_tool import BaseTool


# Constants
VALID_BLAST_TASKS = {
    "blastn",
    "megablast",
    "dc-megablast",
    "blastn-short",
}

DEFAULT_OUTFMT = (
    "6 "
    "qseqid "
    "sseqid "
    "pident "
    "length "
    "mismatch "
    "gapopen "
    "qstart "
    "qend "
    "sstart "
    "send "
    "evalue "
    "bitscore "
    "qcovs "
    "staxids "
    "sscinames "
    "stitle"
)


class BlastRunner(BaseTool):
    """Runner for local BLAST nucleotide searches."""

    def __init__(
        self,
        query_fasta: str | Path,
        database: str | Path,
        output_dir: str | Path,
        working_dir: str | Path,
        sample_id: str,
        threads: int = 4,
        task: str = "blastn",
        output_format: str = DEFAULT_OUTFMT,
        evalue: float = 1e-5,
        max_target_seqs: int = 10,
        max_hsps: int | None = 1,
        perc_identity: float | None = None,
        query_coverage: float | None = None,
        word_size: int | None = None,
        logger: Logger | None = None,
    ) -> None:
        """Initialize BlastRunner.

        Args:
            query_fasta (str | Path): Query mitochondrial genome FASTA.
            database (str | Path): BLAST database prefix.
            output_dir (str | Path): Directory for BLAST results.
            working_dir (str | Path): Working directory for execution.
            sample_id (str): Sample identifier used in output names.
            threads (int, optional): Number of BLAST threads. Defaults to 4.
            task (str, optional): blastn task. Defaults to "blastn".
            output_format (str, optional): BLAST output format.
            evalue (float, optional): Maximum expected value. Defaults to 1e-5.
            max_target_seqs (int, optional): Maximum subject sequences retained.
            max_hsps (int | None, optional): Maximum HSPs per query-subject pair.
            perc_identity (float | None, optional): Minimum percent identity.
            query_coverage (float | None, optional): Minimum HSP query coverage.
            word_size (int | None, optional): BLAST word size.
            logger (Logger | None, optional): Logger object.
        """
        super().__init__(
            tool_name="blast",
            working_dir=Path(working_dir),
            logger=logger,
        )

        # Checking input files and options.
        self.query_fasta = Path(query_fasta)
        self.database = Path(database)
        self.output_dir = Path(output_dir)
        self.sample_id = sample_id

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
        """Validate BLAST input files and options.
        
        Raises:
            FileNotFoundError: Query FASTA does not exist.
            ValueError: Query FASTA is empty.
        """

        # Checking query FASTA.
        if not self.query_fasta.exists():
            self._log_error(
                f"Query FASTA does not exist: {self.query_fasta}"
            )
            raise FileNotFoundError(
                f"({self.tool_name}) Query FASTA does not exist: "
                f"{self.query_fasta}"
            )

        if not self.query_fasta.is_file():
            self._log_error(
                f"Query FASTA is not a file: {self.query_fasta}"
            )
            raise ValueError(
                f"({self.tool_name}) Query FASTA is not a file: "
                f"{self.query_fasta}"
            )

        if self.query_fasta.stat().st_size == 0:
            self._log_error(
                f"Query FASTA is empty: {self.query_fasta}"
            )
            raise ValueError(
                f"({self.tool_name}) Query FASTA is empty: "
                f"{self.query_fasta}"
            )

        # Checking database prefix and required files.
        missing_database_files = [
            path
            for path in self._required_database_files()
            if not path.exists()
        ]

        if missing_database_files:
            self._log_error(
                "BLAST database is incomplete. Missing files: "
                f"{missing_database_files}"
            )
            raise FileNotFoundError(
                f"({self.tool_name}) BLAST database is incomplete. "
                f"Missing files: {missing_database_files}"
            )

        # Checking sample identifier.
        if self.sample_id.strip() == "":
            self._log_error("sample_id must not be empty.")
            raise ValueError(
                f"({self.tool_name}) sample_id must not be empty."
            )

        # Checking threads.
        available_cpus = os.cpu_count()

        if self.threads <= 0:
            self._log_error(
                f"Invalid number of threads: {self.threads}"
            )
            raise ValueError(
                f"({self.tool_name}) Invalid number of threads: "
                f"{self.threads}"
            )

        if available_cpus is not None and self.threads > available_cpus:
            self._log_error(
                "Number of threads exceeds available CPU cores. "
                f"{self.threads} > {available_cpus}"
            )
            raise ValueError(
                f"({self.tool_name}) Number of threads exceeds available "
                f"CPU cores. {self.threads} > {available_cpus}"
            )

        # Checking BLAST task.
        if self.task not in VALID_BLAST_TASKS:
            self._log_error(
                f"Unsupported BLAST task: {self.task}"
            )
            raise ValueError(
                f"({self.tool_name}) Unsupported BLAST task: {self.task}"
            )

        # Checking numeric options.
        if self.evalue <= 0:
            raise ValueError(
                f"({self.tool_name}) evalue must be greater than zero."
            )

        if self.max_target_seqs <= 0:
            raise ValueError(
                f"({self.tool_name}) max_target_seqs must be greater than zero."
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
                f"({self.tool_name}) perc_identity must be between 0 and 100."
            )

        if (
            self.query_coverage is not None
            and not 0 <= self.query_coverage <= 100
        ):
            raise ValueError(
                f"({self.tool_name}) query_coverage must be between 0 and 100."
            )

        if self.word_size is not None and self.word_size <= 0:
            raise ValueError(
                f"({self.tool_name}) word_size must be greater than zero."
            )

    def build_command(self) -> list[str]:
        """Build the local blastn command.

        Returns:
            list[str]: BLAST command.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            "blastn",
            "-query",
            str(self.query_fasta),
            "-db",
            str(self.database),
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
            "-num_threads",
            str(self.threads),
        ]

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
        """Validate BLAST output file."""
        output_file = self._expected_blast_output()

        if not output_file.exists():
            self._log_error(
                f"Expected BLAST output does not exist: {output_file}"
            )
            raise FileNotFoundError(
                f"({self.tool_name}) Expected BLAST output does not exist: "
                f"{output_file}"
            )

        if not output_file.is_file():
            self._log_error(
                f"Expected BLAST output is not a file: {output_file}"
            )
            raise ValueError(
                f"({self.tool_name}) Expected BLAST output is not a file: "
                f"{output_file}"
            )

        # Empty output is valid when BLAST finds no matching sequences.
        if output_file.stat().st_size == 0:
            if self.logger is not None:
                self.logger.warning(
                    f"({self.tool_name}) BLAST completed successfully but "
                    f"returned no hits for sample {self.sample_id}."
                )

    def _expected_blast_output(self) -> Path:
        """Return expected BLAST results path.

        Returns:
            Path: Expected BLAST TSV path.
        """
        return self.output_dir / f"{self.sample_id}.blast.tsv"

    def _required_database_files(self) -> list[Path]:
        """Return required nucleotide BLAST database files.

        Returns:
            list[Path]: Required database component paths.
        """
        prefix = str(self.database)

        return [
            Path(f"{prefix}.nhr"),
            Path(f"{prefix}.nin"),
            Path(f"{prefix}.nsq"),
        ]

    def _log_error(self, message: str) -> None:
        """Log an error when a logger is available."""
        if self.logger is not None:
            self.logger.error(f"({self.tool_name}) {message}")