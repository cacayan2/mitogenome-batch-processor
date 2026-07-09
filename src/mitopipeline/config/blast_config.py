"""blast_config.py

Normalized configuration model for BLAST execution and database setup.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


VALID_BLAST_MODES = {
    "local",
    "remote",
}

VALID_DATABASE_SOURCES = {
    "ncbi",
    "fasta",
}


@dataclass(frozen=True)
class BlastConfig:
    """Normalized BLAST configuration."""

    mode: str
    database_source: str

    database_name: str
    database_dir: Path
    reference_fasta: Path
    database_title: str

    initialize_database: bool
    overwrite_database: bool
    parse_seqids: bool

    threads: int
    task: str
    evalue: float
    max_target_seqs: int
    max_hsps: int | None
    maximum_matches: int

    perc_identity: float | None
    query_coverage: float | None
    word_size: int | None
    output_format: str

    entrez_email: str | None
    entrez_api_key: str | None
    ncbi_query: str
    ncbi_max_records: int
    ncbi_batch_size: int

    @classmethod
    def from_mapping(
        cls,
        config: Mapping[str, Any],
    ) -> "BlastConfig":
        """Create normalized BLAST configuration from a mapping."""
        instance = cls(
            mode=str(
                config.get("mode", "local")
            ),
            database_source=str(
                config.get("database_source", "ncbi")
            ),
            database_name=str(
                config.get("database_name", "mitopipeline_mt_refs")
            ),
            database_dir=Path(
                config.get("database_dir", "resources/blast")
            ),
            reference_fasta=Path(
                config.get(
                    "reference_fasta",
                    "resources/blast/reference_mitogenomes.fasta",
                )
            ),
            database_title=str(
                config.get(
                    "database_title",
                    "MitoPipeline mitochondrial reference database",
                )
            ),
            initialize_database=bool(
                config.get("initialize_database", True)
            ),
            overwrite_database=bool(
                config.get("overwrite_database", False)
            ),
            parse_seqids=bool(
                config.get("parse_seqids", True)
            ),
            threads=int(
                config.get("threads", 4)
            ),
            task=str(
                config.get("task", "blastn")
            ),
            evalue=float(
                config.get("evalue", 1e-5)
            ),
            max_target_seqs=int(
                config.get("max_target_seqs", 50)
            ),
            max_hsps=(
                None
                if config.get("max_hsps") is None
                else int(config["max_hsps"])
            ),
            maximum_matches=int(
                config.get("maximum_matches", 6)
            ),
            perc_identity=(
                None
                if config.get("perc_identity") is None
                else float(config["perc_identity"])
            ),
            query_coverage=(
                None
                if config.get("query_coverage") is None
                else float(config["query_coverage"])
            ),
            word_size=(
                None
                if config.get("word_size") is None
                else int(config["word_size"])
            ),
            output_format=str(
                config.get(
                    "output_format",
                    (
                        "6 qseqid sseqid pident length mismatch gapopen "
                        "qstart qend sstart send evalue bitscore qcovs "
                        "staxids sscinames stitle"
                    ),
                )
            ),
            entrez_email=(
                None
                if config.get("entrez_email") in (None, "")
                else str(config["entrez_email"])
            ),
            entrez_api_key=(
                None
                if config.get("entrez_api_key") in (None, "")
                else str(config["entrez_api_key"])
            ),
            ncbi_query=str(
                config.get(
                    "ncbi_query",
                    (
                        'mitochondrion[filter] AND refseq[filter] '
                        'AND "complete genome"[Title]'
                    ),
                )
            ),
            ncbi_max_records=int(
                config.get("ncbi_max_records", 250)
            ),
            ncbi_batch_size=int(
                config.get("ncbi_batch_size", 50)
            ),
        )

        instance.validate()

        return instance

    def validate(self) -> None:
        """Validate BLAST configuration values."""
        if self.mode not in VALID_BLAST_MODES:
            raise ValueError(
                f"Unsupported BLAST mode: {self.mode}. "
                f"Expected one of {sorted(VALID_BLAST_MODES)}."
            )

        if self.database_source not in VALID_DATABASE_SOURCES:
            raise ValueError(
                f"Unsupported BLAST database source: "
                f"{self.database_source}. Expected one of "
                f"{sorted(VALID_DATABASE_SOURCES)}."
            )

        if not self.database_name.strip():
            raise ValueError(
                "BLAST database_name must not be empty."
            )

        if self.threads <= 0:
            raise ValueError(
                "BLAST threads must be greater than zero."
            )

        if self.evalue <= 0:
            raise ValueError(
                "BLAST evalue must be greater than zero."
            )

        if self.max_target_seqs <= 0:
            raise ValueError(
                "BLAST max_target_seqs must be greater than zero."
            )

        if self.max_hsps is not None and self.max_hsps <= 0:
            raise ValueError(
                "BLAST max_hsps must be greater than zero."
            )

        if self.maximum_matches <= 0:
            raise ValueError(
                "BLAST maximum_matches must be greater than zero."
            )

        if (
            self.perc_identity is not None
            and not 0 <= self.perc_identity <= 100
        ):
            raise ValueError(
                "BLAST perc_identity must be between 0 and 100."
            )

        if (
            self.query_coverage is not None
            and not 0 <= self.query_coverage <= 100
        ):
            raise ValueError(
                "BLAST query_coverage must be between 0 and 100."
            )

        if self.word_size is not None and self.word_size <= 0:
            raise ValueError(
                "BLAST word_size must be greater than zero."
            )

        if self.ncbi_max_records <= 0:
            raise ValueError(
                "BLAST ncbi_max_records must be greater than zero."
            )

        if self.ncbi_batch_size <= 0:
            raise ValueError(
                "BLAST ncbi_batch_size must be greater than zero."
            )

        if self.uses_ncbi_download and not self.entrez_email:
            raise ValueError(
                "Local NCBI mitochondrial reference download requires "
                "tools.blast.entrez_email."
            )

    @property
    def database_prefix(self) -> Path:
        """Return derived local database prefix."""
        return self.database_dir / self.database_name

    @property
    def database_argument(self) -> str:
        """Return value passed to blastn -db."""
        if self.mode == "remote":
            return self.database_name

        return str(
            self.database_prefix.resolve()
        )

    @property
    def requires_database_setup(self) -> bool:
        """Return whether the Snakemake database setup rule is required."""
        return (
            self.mode == "local"
            and self.initialize_database
        )

    @property
    def uses_ncbi_download(self) -> bool:
        """Return whether local NCBI reference FASTA download is selected."""
        return (
            self.mode == "local"
            and self.database_source == "ncbi"
        )

    @property
    def uses_reference_fasta(self) -> bool:
        """Return whether custom FASTA database construction is selected."""
        return (
            self.mode == "local"
            and self.database_source == "fasta"
        )
