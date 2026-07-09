"""fastp.py

API wrapper for paired-end fastp trimming and filtering.
"""

from __future__ import annotations

from logging import Logger
import os
from pathlib import Path

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample


class FastpRunner(BaseTool):
    """Run fastp for one paired-end sample."""

    def __init__(
        self,
        working_dir: Path,
        output_dir: Path,
        sample: Sample,
        tool_options: dict | None = None,
        threads: int = 4,
        logger: Logger | None = None,
        tool_name: str = "fastp",
    ) -> None:
        super().__init__(
            tool_name=tool_name,
            working_dir=Path(working_dir),
            logger=logger,
        )
        self.sample = sample
        self.output_dir = Path(output_dir)
        self.threads = int(threads)
        self.tool_options = tool_options or {}

    @property
    def output_r1(self) -> Path:
        return (
            self.output_dir
            / f"{self.sample.sample_id}_R1.trimmed.fastq.gz"
        )

    @property
    def output_r2(self) -> Path:
        return (
            self.output_dir
            / f"{self.sample.sample_id}_R2.trimmed.fastq.gz"
        )

    @property
    def output_html(self) -> Path:
        return (
            self.output_dir
            / f"{self.sample.sample_id}.fastp.html"
        )

    @property
    def output_json(self) -> Path:
        return (
            self.output_dir
            / f"{self.sample.sample_id}.fastp.json"
        )

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

        available_cpus = os.cpu_count()
        if available_cpus is not None and self.threads > available_cpus:
            raise ValueError(
                f"({self.tool_name}) Threads exceed available CPUs: "
                f"{self.threads} > {available_cpus}."
            )

    def build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.logger is not None:
            self.logger.debug(
                f"({self.tool_name}) Output R1: {self.output_r1}"
            )
            self.logger.debug(
                f"({self.tool_name}) Output R2: {self.output_r2}"
            )
            self.logger.debug(
                f"({self.tool_name}) HTML report: {self.output_html}"
            )
            self.logger.debug(
                f"({self.tool_name}) JSON report: {self.output_json}"
            )

        command = [
            "fastp",
            "--in1",
            str(self.sample.r1),
            "--in2",
            str(self.sample.r2),
            "--out1",
            str(self.output_r1),
            "--out2",
            str(self.output_r2),
            "--html",
            str(self.output_html),
            "--json",
            str(self.output_json),
            "--thread",
            str(self.threads),
        ]

        return self._add_additional_fastp_args(command)

    def validate_outputs(self) -> None:
        for expected_file in self._expected_fastp_outputs():
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

    def _expected_fastp_outputs(self) -> list[Path]:
        return [
            self.output_r1,
            self.output_r2,
            self.output_html,
            self.output_json,
        ]

    def _add_additional_fastp_args(
        self,
        command: list[str],
    ) -> list[str]:
        value_options = {
            "qualified_quality_phred": "--qualified_quality_phred",
            "length_required": "--length_required",
            "trim_front1": "--trim_front1",
            "trim_tail1": "--trim_tail1",
            "trim_front2": "--trim_front2",
            "trim_tail2": "--trim_tail2",
            "cut_window_size": "--cut_window_size",
            "cut_mean_quality": "--cut_mean_quality",
            "n_base_limit": "--n_base_limit",
            "unqualified_percent_limit": "--unqualified_percent_limit",
            "average_qual": "--average_qual",
            "report_title": "--report_title",
            "adapter_sequence": "--adapter_sequence",
            "adapter_sequence_r2": "--adapter_sequence_r2",
            "adapter_fasta": "--adapter_fasta",
        }

        for option_name, flag in value_options.items():
            value = self.tool_options.get(option_name)
            if value is not None:
                command.extend([flag, str(value)])

        boolean_options = {
            "detect_adapter_for_pe": "--detect_adapter_for_pe",
            "cut_front": "--cut_front",
            "cut_tail": "--cut_tail",
            "cut_right": "--cut_right",
            "disable_quality_filtering": "--disable_quality_filtering",
            "disable_length_filtering": "--disable_length_filtering",
            "trim_poly_g": "--trim_poly_g",
            "disable_trim_poly_g": "--disable_trim_poly_g",
            "trim_poly_x": "--trim_poly_x",
        }

        for option_name, flag in boolean_options.items():
            if self.tool_options.get(option_name, False):
                command.append(flag)

        return command
