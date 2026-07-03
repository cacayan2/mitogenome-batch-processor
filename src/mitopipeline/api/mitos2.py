"""mitos2.py

API wrapper for running MITOS2 mitochondrial genome annotation.
"""

# Imports
from pathlib import Path
from logging import Logger
from shutil import which

from mitopipeline.api.base_tool import BaseTool


class MITOS2Runner(BaseTool):
    """Runner for MITOS2 mitochondrial genome annotation."""

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
    ):
        """Initialize MITOS2Runner.

        Args:
            input_fasta (str | Path): Input mitochondrial genome FASTA.
            output_dir (str | Path): MITOS2 output directory.
            working_dir (str | Path): Working directory for command execution.
            genetic_code (int): Mitochondrial genetic code.
            refseqver (str): MITOS2 reference data version.
            refdir (str | Path): Base directory containing MITOS2 reference data.
            circular (bool, optional): Treat genome as circular. Defaults to True.
            noplots (bool, optional): Disable plot generation. Defaults to False.
            zip_output (bool, optional): Create zipped output. Defaults to False.
            best (bool, optional): Annotate only the best copy of each feature. Defaults to False.
            ncbicode (bool, optional): Use NCBI start/stop codons. Defaults to False.
            logger (Logger | None, optional): Logger object. Defaults to None.
        """

        # Initializing parent class.
        super().__init__(
            tool_name="mitos2",
            working_dir=working_dir,
            logger=logger,
        )
        self.conda_env = conda_env

        # Storing paths.
        self.input_fasta = Path(input_fasta)
        self.output_dir = Path(output_dir)
        self.refdir = Path(refdir)

        # Storing required options.
        self.genetic_code = genetic_code
        self.refseqver = refseqver

        # Storing optional behavior.
        self.circular = circular
        self.noplots = noplots
        self.zip_output = zip_output
        self.best = best
        self.ncbicode = ncbicode

    def validate_inputs(self) -> None:
        """Validate MITOS2 input files and options."""
        # Checking input FASTA exists.
        if not self.input_fasta.exists():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Input FASTA does not exist: {self.input_fasta}")
            raise FileNotFoundError(f"({self.tool_name}) Input FASTA does not exist: {self.input_fasta}")

        # Checking input FASTA is a file.
        if not self.input_fasta.is_file():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Input FASTA is not a file: {self.input_fasta}")
            raise ValueError(f"({self.tool_name}) Input FASTA is not a file: {self.input_fasta}")

        # Checking input FASTA is non-empty.
        if self.input_fasta.stat().st_size == 0:
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Input FASTA is empty: {self.input_fasta}")
            raise ValueError(f"({self.tool_name}) Input FASTA is empty: {self.input_fasta}")

        # Checking genetic code.
        if not isinstance(self.genetic_code, int):
            if self.logger is not None: self.logger.error(f"({self.tool_name}) genetic_code must be an integer.")
            raise TypeError(f"({self.tool_name}) genetic_code must be an integer.")

        # Checking reference version.
        if self.refseqver is None or str(self.refseqver).strip() == "":
            if self.logger is not None: self.logger.error(f"({self.tool_name}) refseqver must be provided.")
            raise ValueError(f"({self.tool_name}) refseqver must be provided.")

        # Checking reference root.
        if not self.refdir.exists():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Reference root does not exist: {self.refdir}")
            raise FileNotFoundError(f"({self.tool_name}) Reference root does not exist: {self.refdir}")

        if not self.refdir.is_dir():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Reference root is not a directory: {self.refdir}")
            raise ValueError(f"({self.tool_name}) Reference root is not a directory: {self.refdir}")

        # Checking specific reference version directory.
        refseq_path = self.refdir / self.refseqver

        if not refseq_path.exists():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Reference version does not exist: {refseq_path}")
            raise FileNotFoundError(f"({self.tool_name}) Reference version does not exist: {refseq_path}")

        if not refseq_path.is_dir():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Reference version path is not a directory: {refseq_path}")
            raise ValueError(f"({self.tool_name}) Reference version path is not a directory: {refseq_path}")

    def build_command(self) -> list[str]:
        """Build the MITOS2 command.

        Returns:
            list[str]: MITOS2 command.
        """

        # Creating output directory.
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Creating base command.
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
        
        # Adding optional flags.
        if not self.circular:
            command.append("--linear")

        if self.noplots:
            command.append("--noplots")

        if self.best:
            command.append("--best")

        if self.ncbicode:
            command.append("--ncbicode")

        # Returning command.
        return command

    def validate_outputs(self) -> None:
        """Validate deterministic MITOS2 annotation outputs."""
        # Checking output directory exists.
        if not self.output_dir.exists():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Output directory does not exist: {self.output_dir}")
            raise FileNotFoundError(f"({self.tool_name}) Output directory does not exist: {self.output_dir}")

        # Defining required final output files observed from successful MITOS2 run.
        required_files = [
            self.output_dir / "result.bed",
            self.output_dir / "result.faa",
            self.output_dir / "result.fas",
            self.output_dir / "result.geneorder",
            self.output_dir / "result.gff",
            self.output_dir / "result.mitos",
            self.output_dir / "result.seq",
        ]

        # Checking required files exist and are non-empty.
        for required_file in required_files:
            if not required_file.exists():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output file does not exist: {required_file}")
                raise FileNotFoundError(f"({self.tool_name}) Expected output file does not exist: {required_file}")

            if not required_file.is_file():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output is not a file: {required_file}")
                raise ValueError(f"({self.tool_name}) Expected output is not a file: {required_file}")

        # Optional check for stst.dat.
        status_file = self.output_dir / "stst.dat"

        if not status_file.exists():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected status file does not exist: {status_file}")
            raise FileNotFoundError(f"({self.tool_name}) Expected status file does not exist: {status_file}")

        if not status_file.is_file():
            if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected status path is not a file: {status_file}")
            raise ValueError(f"({self.tool_name}) Expected status path is not a file: {status_file}")

        # Checking required intermediate directories exist.
        required_directories = [
            self.output_dir / "blast",
            self.output_dir / "blast" / "prot",
            self.output_dir / "blast" / "nuc",
            self.output_dir / "mitfi-global",
        ]

        for required_directory in required_directories:
            if not required_directory.exists():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output directory does not exist: {required_directory}")
                raise FileNotFoundError(f"({self.tool_name}) Expected output directory does not exist: {required_directory}")

            if not required_directory.is_dir():
                if self.logger is not None: self.logger.error(f"({self.tool_name}) Expected output path is not a directory: {required_directory}")
                raise ValueError(f"({self.tool_name}) Expected output path is not a directory: {required_directory}")

        # Checking annotation files contain useful content.
        self._validate_gff(self.output_dir / "result.gff")
        self._validate_fasta(self.output_dir / "result.fas")
        self._validate_fasta(self.output_dir / "result.faa")

    def _validate_gff(self, gff_path: Path) -> None:
        """Validate that a GFF file contains annotation rows.

        Args:
            gff_path (Path): Path to GFF file.
        """
        # Counting non-comment feature rows.
        feature_count = 0

        with gff_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.strip() == "":
                    continue

                if line.startswith("#"):
                    continue

                feature_count += 1

        if feature_count == 0:
            if self.logger is not None: self.logger.error(f"({self.tool_name}) GFF file contains no feature rows: {gff_path}")
            raise ValueError(f"({self.tool_name}) GFF file contains no feature rows: {gff_path}")

    def _validate_fasta(self, fasta_path: Path) -> None:
        """Validate that a FASTA file contains at least one sequence record.

        Args:
            fasta_path (Path): Path to FASTA file.
        """
        # Checking for FASTA headers.
        header_count = 0

        with fasta_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith(">"):
                    header_count += 1

        if header_count == 0:
            raise ValueError(f"({self.tool_name}) FASTA file contains no sequence records: {fasta_path}")