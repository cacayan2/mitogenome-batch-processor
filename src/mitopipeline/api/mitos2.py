"""mitos2.py

API wrapper for running MITOS2 mitochondrial genome annotation.

MITOS2 may leave partial output directories even when final result files are
not produced. This runner treats missing/empty final result files as failures.
"""

from __future__ import annotations

from logging import Logger
from pathlib import Path

from mitopipeline.api.base_tool import BaseTool


class MITOS2Runner(BaseTool):
    """Runner for MITOS2 mitochondrial genome annotation."""

    REQUIRED_RESULT_FILES = (
        "result.bed",
        "result.faa",
        "result.fas",
        "result.geneorder",
        "result.gff",
        "result.mitos",
        "result.seq",
    )

    def __init__(
        self,
        input_fasta: str | Path,
        output_dir: str | Path,
        working_dir: str | Path,
        genetic_code: int,
        refseqver: str,
        refdir: str | Path,
        circular: bool = True,
        noplots: bool = False,
        zip_output: bool = False,
        best: bool = False,
        ncbicode: bool = False,
        logger: Logger | None = None,
        conda_env: str = "mito-annotation",
    ) -> None:
        """Initialize MITOS2Runner."""
        super().__init__(
            tool_name="mitos2",
            working_dir=Path(working_dir),
            logger=logger,
        )

        self.conda_env = conda_env
        self.input_fasta = Path(input_fasta)
        self.output_dir = Path(output_dir)
        self.refdir = Path(refdir)
        self.genetic_code = genetic_code
        self.refseqver = refseqver
        self.circular = circular
        self.noplots = noplots
        self.zip_output = zip_output
        self.best = best
        self.ncbicode = ncbicode

    def validate_inputs(self) -> None:
        """Validate MITOS2 input files and options."""
        if not self.input_fasta.exists():
            raise FileNotFoundError(
                f"({self.tool_name}) Input FASTA does not exist: "
                f"{self.input_fasta}"
            )

        if not self.input_fasta.is_file():
            raise ValueError(
                f"({self.tool_name}) Input FASTA is not a file: "
                f"{self.input_fasta}"
            )

        if self.input_fasta.stat().st_size == 0:
            raise ValueError(
                f"({self.tool_name}) Input FASTA is empty: "
                f"{self.input_fasta}"
            )

        if not isinstance(self.genetic_code, int):
            raise TypeError(
                f"({self.tool_name}) genetic_code must be an integer."
            )

        if self.refseqver is None or str(self.refseqver).strip() == "":
            raise ValueError(
                f"({self.tool_name}) refseqver must be provided."
            )

        if not self.refdir.exists() or not self.refdir.is_dir():
            raise FileNotFoundError(
                f"({self.tool_name}) Reference root is missing or not a "
                f"directory: {self.refdir}"
            )

        refseq_path = self.refdir / self.refseqver
        if not refseq_path.exists() or not refseq_path.is_dir():
            raise FileNotFoundError(
                f"({self.tool_name}) Reference version is missing or not a "
                f"directory: {refseq_path}"
            )

    def build_command(self) -> list[str]:
        """Build the MITOS2 command."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.logger is not None:
            self.logger.debug(
                f"({self.tool_name}) Input FASTA: {self.input_fasta}"
            )
            self.logger.debug(
                f"({self.tool_name}) Output directory: {self.output_dir}"
            )
            self.logger.debug(
                f"({self.tool_name}) Reference directory: {self.refdir}"
            )
            self.logger.debug(
                f"({self.tool_name}) Reference version: {self.refseqver}"
            )

        command = [
            "conda",
            "run",
            "-n",
            self.conda_env,
            "runmitos.py",
            "-i",
            str(self.input_fasta),
            "--code",
            str(self.genetic_code),
            "--outdir",
            str(self.output_dir),
            "--refdir",
            str(self.refdir),
            "--refseqver",
            str(self.refseqver),
        ]

        if not self.circular:
            command.append("--linear")

        if self.noplots:
            command.append("--noplots")

        if self.best:
            command.append("--best")

        if self.ncbicode:
            command.append("--ncbicode")

        if self.zip_output:
            command.append("--zip")

        return command

    def validate_outputs(self) -> None:
        """Validate completed MITOS2 annotation outputs."""
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError(
                f"({self.tool_name}) Output directory does not exist: "
                f"{self.output_dir}"
            )

        missing_files = []
        empty_files = []

        for filename in self.REQUIRED_RESULT_FILES:
            path = self.output_dir / filename

            if not path.exists() or not path.is_file():
                missing_files.append(str(path))
                continue

            if path.stat().st_size == 0:
                empty_files.append(str(path))

        if missing_files:
            observed = sorted(p.name for p in self.output_dir.iterdir())
            raise FileNotFoundError(
                f"({self.tool_name}) MITOS2 did not produce required "
                f"annotation files. Missing: {missing_files}. "
                f"Observed in output directory: {observed}"
            )

        if empty_files:
            raise ValueError(
                f"({self.tool_name}) MITOS2 produced empty required files: "
                f"{empty_files}"
            )

        status_file = self.output_dir / "stst.dat"
        if not status_file.exists() or not status_file.is_file():
            raise FileNotFoundError(
                f"({self.tool_name}) Expected status file is missing: "
                f"{status_file}"
            )

        self._validate_gff(self.output_dir / "result.gff")
        self._validate_fasta(self.output_dir / "result.fas")
        self._validate_fasta(self.output_dir / "result.faa")

    def _validate_gff(self, gff_path: Path) -> None:
        """Validate that a GFF file contains annotation rows."""
        feature_count = 0

        with gff_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.strip() and not line.startswith("#"):
                    feature_count += 1

        if feature_count == 0:
            raise ValueError(
                f"({self.tool_name}) GFF contains no feature rows: "
                f"{gff_path}"
            )

    def _validate_fasta(self, fasta_path: Path) -> None:
        """Validate that a FASTA file contains at least one sequence record."""
        header_count = 0

        with fasta_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith(">"):
                    header_count += 1

        if header_count == 0:
            raise ValueError(
                f"({self.tool_name}) FASTA contains no sequence records: "
                f"{fasta_path}"
            )
