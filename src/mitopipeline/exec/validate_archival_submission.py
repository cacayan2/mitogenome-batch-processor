"""Command-line execution layer for archival readiness validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.archival.validation import (
    write_archival_validation_outputs,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate NCBI archival readiness across raw FASTQ, assembly, "
            "annotation, BioSample, SRA, and mitogenome metadata."
        )
    )
    parser.add_argument(
        "--runtime-manifest",
        required=True,
    )
    parser.add_argument(
        "--job-directory",
        required=True,
    )
    parser.add_argument(
        "--summary-output",
        required=True,
    )
    parser.add_argument(
        "--report-output",
        required=True,
    )
    parser.add_argument(
        "--submission-directory",
        default=None,
    )
    parser.add_argument(
        "--log-file",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    """Run archival validation."""
    args = parse_args()
    logger = make_logger(
        name="archival_validation",
        log_file_path=args.log_file,
    )

    try:
        write_archival_validation_outputs(
            runtime_manifest_path=Path(
                args.runtime_manifest
            ),
            job_directory=Path(
                args.job_directory
            ),
            submission_directory=(
                Path(
                    args.submission_directory
                )
                if args.submission_directory is not None
                else None
            ),
            summary_output_path=Path(
                args.summary_output
            ),
            report_output_path=Path(
                args.report_output
            ),
            logger=logger,
        )
        return 0

    except Exception as error:
        logger.exception(
            "Archival validation failed: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
