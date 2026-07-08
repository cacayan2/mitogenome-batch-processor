"""report_data.py

Data model containing all information used in one sample report.
"""

# Imports
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SampleReportData:
    """Aggregated pipeline results for one sample."""

    sample_id: str
    metadata: dict[str, str]
    fastp_stats: dict[str, Any] | None
    assembly_stats: dict[str, Any] | None
    annotation_stats: dict[str, Any] | None
    blast_matches: list[dict] | None
    phylogeny_model: str | None
    phylogeny_tip_count: int | None
    output_paths: dict[str, Path]