"""API wrapper for MITOS2 annotation."""

from __future__ import annotations

from logging import Logger
from pathlib import Path
import subprocess

from mitopipeline.api.base_tool import BaseTool


class MITOS2Runner(BaseTool):
    REQUIRED_RESULT_FILES = (
        "result.bed", "result.faa", "result.fas", "result.geneorder",
        "result.gff", "result.mitos", "result.seq",
    )

    def __init__(
        self, input_fasta, output_dir, working_dir, genetic_code,
        refseqver, refdir, sample_id, circular=True, noplots=False,
        zip_output=False, best=False, ncbicode=False, logger: Logger | None = None,
        conda_env="mito-annotation",
    ):
        super().__init__("mitos2", Path(working_dir), logger)
        self.sample_id = sample_id
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
        self.mitos_executable = None

    def validate_inputs(self):
        if not self.input_fasta.is_file():
            raise FileNotFoundError(f"(mitos2) Input FASTA missing: {self.input_fasta}")
        if self.input_fasta.stat().st_size == 0:
            raise ValueError(f"(mitos2) Input FASTA empty: {self.input_fasta}")

        refseq_path = self.refdir / self.refseqver
        ready_file = refseq_path / ".mitopipeline_reference_ready"

        if not refseq_path.is_dir():
            raise FileNotFoundError(f"(mitos2) Reference directory missing: {refseq_path}")
        if not ready_file.is_file():
            raise FileNotFoundError(f"(mitos2) Reference validation marker missing: {ready_file}")

        self.mitos_executable = self._resolve_executable()

    def build_command(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            "conda", "run", "-n", self.conda_env,
            self.mitos_executable or "runmitos",
            "-i", str(self.input_fasta),
            "--code", str(self.genetic_code),
            "--outdir", str(self.output_dir),
            "--refdir", str(self.refdir),
            "--refseqver", str(self.refseqver),
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

    def validate_outputs(self):
        for filename in self.REQUIRED_RESULT_FILES:
            path = self.output_dir / filename
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError(f"(mitos2) Missing or empty output: {path}")

    def _resolve_executable(self):
        for executable in ("runmitos", "runmitos.py"):
            result = subprocess.run(
                ["conda", "run", "-n", self.conda_env, executable, "--help"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return executable
        raise RuntimeError("Neither runmitos nor runmitos.py is available.")
