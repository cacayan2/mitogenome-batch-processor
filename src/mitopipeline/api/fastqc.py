"""Parallel-safe FastQC wrapper using one sample directory."""

from __future__ import annotations

from logging import Logger
from pathlib import Path
import shutil

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample


class FastQCRunner(BaseTool):
    """Run FastQC and normalize outputs inside one sample directory."""

    def __init__(
        self,
        working_dir: Path,
        output_dir: Path,
        sample: Sample,
        r1_output_stem: str,
        r2_output_stem: str,
        logger: Logger | None = None,
        tool_name: str = "fastqc",
        threads: int = 4,
    ) -> None:
        super().__init__(
            tool_name=tool_name,
            working_dir=Path(working_dir),
            logger=logger,
        )
        self.output_dir = Path(output_dir)
        self.sample = sample
        self.r1_output_stem = r1_output_stem
        self.r2_output_stem = r2_output_stem
        self.threads = int(threads)

    def validate_inputs(self) -> None:
        for path in (self.sample.r1, self.sample.r2):
            if not path.is_file():
                if self.logger is not None: self.logger.error(f"Input file not found: {path}")
                raise FileNotFoundError(
                    f"({self.tool_name}) Input file not found: {path}"
                )

        if self.threads <= 0:
            if self.logger is not None: self.logger.error("threads must be greater than zero.")
            raise ValueError("threads must be greater than zero.")

    def build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        return [
            "fastqc",
            "--threads",
            str(self.threads),
            str(self.sample.r1),
            str(self.sample.r2),
            "-o",
            str(self.output_dir),
        ]

    def postprocess_outputs(self) -> None:
        sources = [
            *self._native_outputs(self.sample.r1),
            *self._native_outputs(self.sample.r2),
        ]
        targets = self._expected_fastqc_outputs()

        for source, target in zip(sources, targets, strict=True):
            if not source.is_file():
                if self.logger is not None: self.logger.error(f"Native FastQC output missing: {source}")
                raise FileNotFoundError(
                    f"({self.tool_name}) Native FastQC output missing: "
                    f"{source}"
                )

            if source != target:
                shutil.move(str(source), str(target))

    def validate_outputs(self) -> None:
        for path in self._expected_fastqc_outputs():
            if not path.is_file() or path.stat().st_size == 0:
                if self.logger is not None: self.logger.error(f"Missing or empty output: {path}")
                raise FileNotFoundError(
                    f"({self.tool_name}) Missing or empty output: {path}"
                )

    def _native_outputs(self, fastq: Path) -> tuple[Path, Path]:
        stem = self._strip_fastq_suffix(fastq)
        return (
            self.output_dir / f"{stem}_fastqc.html",
            self.output_dir / f"{stem}_fastqc.zip",
        )

    def _expected_fastqc_outputs(self) -> list[Path]:
        return [
            self.output_dir / f"{self.r1_output_stem}_fastqc.html",
            self.output_dir / f"{self.r1_output_stem}_fastqc.zip",
            self.output_dir / f"{self.r2_output_stem}_fastqc.html",
            self.output_dir / f"{self.r2_output_stem}_fastqc.zip",
        ]

    @staticmethod
    def _strip_fastq_suffix(path: Path) -> str:
        name = path.name

        for suffix in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
            if name.endswith(suffix):
                return name[:-len(suffix)]

        return path.stem
