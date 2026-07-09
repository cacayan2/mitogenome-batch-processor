"""run_report_data.py

Aggregate per-sample pipeline outputs into run-level report data.
"""

# Imports
import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mitopipeline.models.run_report_data import (
    RunReportData,
    SampleRunStatus,
)
from mitopipeline.reporting.report_data import collect_sample_report_data


STAGE_DONE_PATHS = {
    "qc_raw": ("qc", "raw", "{sample}.qc.raw.done"),
    "trimming": ("trimming", "{sample}.trimming.done"),
    "qc_trimmed": ("qc", "trimmed", "{sample}.qc.trimmed.done"),
    "assembly": ("assembly", "{sample}.assembly.done"),
    "annotation": ("annotation", "{sample}.annotation.done"),
    "phylogeny": ("phylogeny", "figures", "{sample}.phylogeny.done"),
    "reporting": ("reporting", "{sample}.report.md"),
}


def read_runtime_manifest_rows(runtime_manifest_path: str | Path) -> list[dict[str, str]]:
    """Read all rows from the runtime manifest."""
    runtime_manifest_path = Path(runtime_manifest_path)

    if not runtime_manifest_path.exists():
        raise FileNotFoundError(
            f"Runtime manifest not found: {runtime_manifest_path}."
        )

    with runtime_manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [
            {
                key: (value.strip() if value is not None else "")
                for key, value in row.items()
            }
            for row in reader
        ]

    if not rows:
        raise ValueError(
            f"Runtime manifest contains no samples: {runtime_manifest_path}."
        )

    return rows


def get_manifest_sample_ids(runtime_manifest_path: str | Path) -> list[str]:
    """Return sample IDs from the runtime manifest."""
    rows = read_runtime_manifest_rows(runtime_manifest_path)
    sample_ids = [row["sample_id"] for row in rows]

    if any(not sample_id for sample_id in sample_ids):
        raise ValueError("Runtime manifest contains an empty sample_id.")

    return sample_ids


def sample_stage_done_path(job_directory: str | Path, sample_id: str, stage_name: str) -> Path:
    """Return the expected completion marker for a sample stage."""
    if stage_name not in STAGE_DONE_PATHS:
        raise ValueError(f"Unsupported stage for run reporting: {stage_name}.")

    path_parts = [
        part.format(sample=sample_id)
        for part in STAGE_DONE_PATHS[stage_name]
    ]

    return Path(job_directory, *path_parts)


def normalize_enabled_stages(enabled_stages: list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize enabled stage names for run reporting."""
    if enabled_stages is None:
        return []

    normalized = []

    for stage_name in enabled_stages:
        stage_name = str(stage_name).strip()

        if not stage_name:
            continue

        if stage_name not in STAGE_DONE_PATHS:
            raise ValueError(f"Unsupported stage for run reporting: {stage_name}.")

        normalized.append(stage_name)

    return normalized


def collect_sample_run_status(sample_id: str, job_directory: str | Path, enabled_stages: list[str]) -> SampleRunStatus:
    """Collect completion-marker status for one sample."""
    job_directory = Path(job_directory)
    stage_statuses: dict[str, str] = {}
    failed_stages: list[str] = []

    for stage_name in enabled_stages:
        done_path = sample_stage_done_path(
            job_directory=job_directory,
            sample_id=sample_id,
            stage_name=stage_name,
        )

        if done_path.exists():
            stage_statuses[stage_name] = "complete"
        else:
            stage_statuses[stage_name] = "missing"
            failed_stages.append(stage_name)

    sample_report_path = job_directory / "reporting" / f"{sample_id}.report.md"

    return SampleRunStatus(
        sample_id=sample_id,
        stage_statuses=stage_statuses,
        completed_stages=sum(status == "complete" for status in stage_statuses.values()),
        expected_stages=len(enabled_stages),
        failed_stages=failed_stages,
        sample_report_path=(sample_report_path if sample_report_path.exists() else None),
    )


def summarize_stage_totals(sample_statuses: list[SampleRunStatus], enabled_stages: list[str]) -> dict[str, dict[str, int]]:
    """Summarize complete and missing counts per stage."""
    totals: dict[str, dict[str, int]] = {}

    for stage_name in enabled_stages:
        complete = sum(
            sample_status.stage_statuses.get(stage_name) == "complete"
            for sample_status in sample_statuses
        )
        missing = sum(
            sample_status.stage_statuses.get(stage_name) == "missing"
            for sample_status in sample_statuses
        )

        totals[stage_name] = {
            "complete": complete,
            "missing": missing,
            "total": len(sample_statuses),
        }

    return totals


def read_run_metadata(job_directory: str | Path) -> dict[str, Any]:
    """Read optional job-level metadata if present."""
    job_directory = Path(job_directory)
    candidate_paths = [
        job_directory / "metadata" / "job_metadata.json",
        job_directory / "metadata" / "metadata.json",
        job_directory / "job_metadata.json",
    ]

    for candidate_path in candidate_paths:
        if not candidate_path.exists():
            continue

        with candidate_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        if isinstance(data, dict):
            return data

    return {}


def build_run_output_paths(job_directory: str | Path) -> dict[str, Path]:
    """Build known run-level output paths."""
    job_directory = Path(job_directory)
    return {
        "runtime_manifest": job_directory / "validated_samples.tsv",
        "run_report": job_directory / "reporting" / "run_report.md",
        "reporting_directory": job_directory / "reporting",
        "logs_directory": job_directory / "logs",
        "assembly_directory": job_directory / "assembly",
        "annotation_directory": job_directory / "annotation",
        "phylogeny_directory": job_directory / "phylogeny",
    }


def collect_run_report_data(
        job_id: str,
        job_directory: str | Path,
        enabled_stages: list[str] | tuple[str, ...] | None,
        logger: logging.Logger | None = None,
) -> RunReportData:
    """Collect all information needed for a run-level report."""
    job_directory = Path(job_directory).resolve()
    output_paths = build_run_output_paths(job_directory)
    runtime_manifest_path = output_paths["runtime_manifest"]
    manifest_rows = read_runtime_manifest_rows(runtime_manifest_path)
    sample_ids = [row["sample_id"] for row in manifest_rows]
    metadata_columns = list(manifest_rows[0].keys())
    enabled_stages = normalize_enabled_stages(enabled_stages)

    sample_data = [
        collect_sample_report_data(
            sample_id=sample_id,
            job_directory=job_directory,
            logger=logger,
        )
        for sample_id in sample_ids
    ]

    sample_statuses = [
        collect_sample_run_status(
            sample_id=sample_id,
            job_directory=job_directory,
            enabled_stages=enabled_stages,
        )
        for sample_id in sample_ids
    ]

    stage_totals = summarize_stage_totals(
        sample_statuses=sample_statuses,
        enabled_stages=enabled_stages,
    )
    run_metadata = read_run_metadata(job_directory)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if logger is not None:
        logger.info(f"Collected run report data for {len(sample_ids)} samples.")

    return RunReportData(
        job_id=job_id,
        job_directory=job_directory,
        runtime_manifest_path=runtime_manifest_path,
        generated_at=generated_at,
        total_samples=len(sample_ids),
        sample_data=sample_data,
        sample_statuses=sample_statuses,
        stage_totals=stage_totals,
        output_paths=output_paths,
        metadata_columns=metadata_columns,
        run_metadata=run_metadata,
    )
