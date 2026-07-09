"""run_report_data.py

Data models for run-level reporting.
"""

# Imports
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mitopipeline.models.report_data import SampleReportData


@dataclass(frozen=True)
class SampleRunStatus:
    """Execution status summary for one sample."""

    sample_id: str
    stage_statuses: dict[str, str]
    completed_stages: int
    expected_stages: int
    failed_stages: list[str]
    sample_report_path: Path | None

    @property
    def overall_status(self) -> str:
        """Return the overall sample status."""
        if self.expected_stages == 0:
            return "not_requested"

        if self.completed_stages == self.expected_stages:
            return "success"

        return "incomplete"


@dataclass(frozen=True)
class RunReportData:
    """Aggregated data for one full pipeline run."""

    job_id: str
    job_directory: Path
    runtime_manifest_path: Path
    generated_at: str
    total_samples: int
    sample_data: list[SampleReportData]
    sample_statuses: list[SampleRunStatus]
    stage_totals: dict[str, dict[str, int]]
    output_paths: dict[str, Path]
    metadata_columns: list[str]
    run_metadata: dict[str, Any]
