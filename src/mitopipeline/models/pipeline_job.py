"""pipeline_job.py

Pipeline job lifecycle and metadata tracking.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import logging
import uuid

from mitopipeline.logging.logger_factory import make_logger


class PipelineJob:
    """Manages the lifecycle and job metadata for one pipeline run."""

    def __init__(
            self,
            parent_dir: Path,
            job_id: str | None = None,
            samples: list[str] | None = None,
    ):
        """Initialize a PipelineJob.

        Samples may be unknown when the launcher first creates the job.
        In that case, start with an empty list and let the launcher update
        samples after preparing the runtime manifest.
        """
        self.is_new_job = True

        if job_id is not None:
            self.is_new_job = False
            self.job_id = job_id
        else:
            now = datetime.now()
            self.job_id = (
                f"{now.strftime('%Y%m%d')}_"
                f"{now.strftime('%H%M')}_"
                f"{uuid.uuid4()}"
            )

        self.samples = (
            list(samples)
            if samples is not None
            else []
        )

        self.start_time = datetime.now()
        self.end_time = None
        self.created_time = None
        self.failed_time = None
        self.runtime = None
        self.parent_dir = Path(
            parent_dir
        )
        self.job_dir = (
            self.parent_dir
            / self.job_id
        )
        self.job_logger = self.create_output_directory()
        self.job_logger.info(
            f"({self.job_id}) Pipeline job {self.job_id} "
            f"started at {self.start_time}."
        )

        self.mark_created()

    def create_output_directory(self) -> logging.Logger:
        """Create canonical output directories and return a job logger."""
        self.parent_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.job_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        directories = [
            self.job_dir / "logs",
            self.job_dir / "logs" / "archival",
            self.job_dir / "metadata",

            # Canonical QC layout used by Snakemake rules.
            self.job_dir / "qc" / "raw",
            self.job_dir / "qc" / "trimmed",

            self.job_dir / "trimming",
            self.job_dir / "assembly",
            self.job_dir / "annotation",
            self.job_dir / "visualization",
            self.job_dir / "phylogeny",
            self.job_dir / "reporting",
            self.job_dir / "stats",
            self.job_dir / "setup",
            self.job_dir / "submission",
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        return make_logger(
            name=self.job_id,
            log_file_path=(
                self.job_dir
                / "logs"
                / "pipeline_job.log"
            ),
        )

    def set_samples(
            self,
            samples: list[str],
    ) -> None:
        """Update job sample IDs."""
        self.samples = list(
            samples
        )

    def _metadata_payload(
            self,
            event_time: datetime,
            status: str,
    ) -> dict:
        """Build a standard metadata payload."""
        runtime = (
            event_time
            - self.start_time
        )

        return {
            "job_id": self.job_id,
            "start_time": self.start_time.isoformat(),
            "event_time": event_time.isoformat(),
            "runtime_seconds": runtime.total_seconds(),
            "output_dir": str(self.job_dir),
            "sample_count": len(self.samples),
            "samples": self.samples,
            "status": status,
        }

    def mark_created(self) -> None:
        """Mark the pipeline job as created and write metadata."""
        self.created_time = datetime.now()
        self.runtime = (
            self.created_time
            - self.start_time
        )

        data = self._metadata_payload(
            event_time=self.created_time,
            status="created",
        )

        if self.is_new_job:
            self.job_logger.info(
                f"({self.job_id}) Pipeline job {self.job_id} "
                f"is a new job, new directory was successfully created "
                f"at {self.job_dir}."
            )
        else:
            self.job_logger.info(
                f"({self.job_id}) Pipeline job {self.job_id} "
                f"already exists, using existing directory and "
                f"automatically progressing pipeline from previous run "
                f"({self.job_dir})."
            )

        self.write_metadata(
            data
        )

    def mark_completed(self) -> None:
        """Mark the pipeline job as completed."""
        self.end_time = datetime.now()
        self.runtime = (
            self.end_time
            - self.start_time
        )

        data = self._metadata_payload(
            event_time=self.end_time,
            status="completed",
        )

        self.job_logger.info(
            f"({self.job_id}) Pipeline job {self.job_id} "
            f"completed at {self.end_time}."
        )
        self.write_metadata(
            data
        )

    def mark_failed(self) -> None:
        """Mark the pipeline job as failed."""
        self.failed_time = datetime.now()
        self.runtime = (
            self.failed_time
            - self.start_time
        )

        data = self._metadata_payload(
            event_time=self.failed_time,
            status="failed",
        )

        self.job_logger.info(
            f"({self.job_id}) Pipeline job {self.job_id} "
            f"failed at {self.failed_time}. Job details can be found "
            f"in {self.job_dir}."
        )
        self.write_metadata(
            data
        )

    def write_metadata(
            self,
            data: dict,
    ) -> None:
        """Write live metadata and append event history."""
        live_file = (
            self.job_dir
            / "job_metadata.json"
        )
        history_file = (
            self.job_dir
            / "job_events.json"
        )

        with live_file.open(
                "w",
                encoding="utf-8",
        ) as handle:
            json.dump(
                data,
                handle,
                indent=4,
            )

        if not history_file.exists():
            history_file.write_text(
                "[]",
                encoding="utf-8",
            )

        with history_file.open(
                "r+",
                encoding="utf-8",
        ) as handle:
            try:
                history_data = json.load(
                    handle
                )
            except json.JSONDecodeError:
                history_data = []

            history_data.append(
                data
            )

            handle.seek(
                0
            )
            json.dump(
                history_data,
                handle,
                indent=4,
            )
            handle.truncate()

        self.job_logger.info(
            f"({self.job_id}) Wrote job metadata to "
            f"{live_file} and {history_file}."
        )
