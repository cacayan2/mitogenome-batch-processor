"""API wrapper for paired-end fastp trimming."""

from __future__ import annotations

from logging import Logger
import os
from pathlib import Path

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.sample import Sample


class FastpRunner(BaseTool):
    """Run fastp for one sample."""

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
        return self.output_dir / "R1.trimmed.fastq.gz"

    @property
    def output_r2(self) -> Path:
        return self.output_dir / "R2.trimmed.fastq.gz"

    @property
    def output_html(self) -> Path:
        return self.output_dir / "fastp.html"

    @property
    def output_json(self) -> Path:
        return self.output_dir / "fastp.json"

    def validate_inputs(self) -> None:
        for path in (self.sample.r1, self.sample.r2):
            if not path.is_file():
                raise FileNotFoundError(
                    f"({self.tool_name}) Input file not found: {path}"
                )

        if self.threads <= 0:
            raise ValueError("threads must be greater than zero.")

        cpus = os.cpu_count()
        if cpus is not None and self.threads > cpus:
            raise ValueError(
                f"threads exceed available CPUs: {self.threads} > {cpus}"
            )

    def build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

        return self._add_options(command)

    def validate_outputs(self) -> None:
        for path in (
            self.output_r1,
            self.output_r2,
            self.output_html,
            self.output_json,
        ):
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError(
                    f"({self.tool_name}) Missing or empty output: {path}"
                )

    def _add_options(self, command: list[str]) -> list[str]:
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

        for key, flag in value_options.items():
            value = self.tool_options.get(key)
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

        for key, flag in boolean_options.items():
            if self.tool_options.get(key, False):
                command.append(flag)

        return command
