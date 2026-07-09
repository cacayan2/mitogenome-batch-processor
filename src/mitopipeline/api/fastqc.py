"""fastqc.py

Parallel-safe API wrapper for FastQC.
"""

from __future__ import annotations

from logging import Logger
from pathlib import Path
import shutil

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample


class FastQCRunner(BaseTool):
    """Run FastQC on paired-end reads."""

    def __init__(
        self,
        working_dir: Path,
        output_dir: Path,
        final_output_dir: Path,
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
        self.sample = sample
        self.output_dir = Path(output_dir)
        self.final_output_dir = Path(final_output_dir)
        self.r1_output_stem = r1_output_stem
        self.r2_output_stem = r2_output_stem
        self.threads = int(threads)

    def validate_inputs(self) -> None:
        for read_path in (self.sample.r1, self.sample.r2):
            if not read_path.exists() or not read_path.is_file():
                raise FileNotFoundError(
                    f"({self.tool_name}) Input FASTQ does not exist: "
                    f"{read_path}"
                )

        if self.threads <= 0:
            raise ValueError(
                f"({self.tool_name}) Invalid thread count: {self.threads}."
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
        native_r1 = self._native_outputs(self.sample.r1)
        native_r2 = self._native_outputs(self.sample.r2)
        final_outputs = self._expected_fastqc_outputs()

        pairs = [
            (native_r1[0], final_outputs[0]),
            (native_r1[1], final_outputs[1]),
            (native_r2[0], final_outputs[2]),
            (native_r2[1], final_outputs[3]),
        ]

        for source, target in pairs:
            if not source.exists():
                raise FileNotFoundError(
                    f"({self.tool_name}) Native FastQC output missing: "
                    f"{source}"
                )

            shutil.copy2(source, target)

            if self.logger is not None:
                self.logger.debug(
                    f"({self.tool_name}) Normalized output: "
                    f"{source} -> {target}"
                )

    def validate_outputs(self) -> None:
        for expected_file in self._expected_fastqc_outputs():
            if not expected_file.exists():
                raise FileNotFoundError(
                    f"({self.tool_name}) Expected output missing: "
                    f"{expected_file}"
                )
            if expected_file.stat().st_size == 0:
                raise ValueError(
                    f"({self.tool_name}) Expected output is empty: "
                    f"{expected_file}"
                )

    def _native_outputs(self, fastq: Path) -> tuple[Path, Path]:
        stem = self._strip_fastq_suffix(fastq)
        return (
            self.output_dir / f"{stem}_fastqc.html",
            self.output_dir / f"{stem}_fastqc.zip",
        )

    def _expected_fastqc_outputs(self) -> list[Path]:
        return [
            self.final_output_dir
            / f"{self.r1_output_stem}_fastqc.html",
            self.final_output_dir
            / f"{self.r1_output_stem}_fastqc.zip",
            self.final_output_dir
            / f"{self.r2_output_stem}_fastqc.html",
            self.final_output_dir
            / f"{self.r2_output_stem}_fastqc.zip",
        ]

    @staticmethod
    def _strip_fastq_suffix(fastq: Path) -> str:
        name = fastq.name
        for suffix in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
            if name.endswith(suffix):
                return name[:-len(suffix)]
        return fastq.stem
