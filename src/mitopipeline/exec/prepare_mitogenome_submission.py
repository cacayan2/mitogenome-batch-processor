"""Command-line execution layer for mitogenome archival preparation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mitopipeline.archival.mitogenome_metadata import (
    write_mitogenome_submission,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Collect assembled mitogenome FASTA and MITOS2 annotation "
            "outputs into a reviewable NCBI submission directory."
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
        "--output-directory",
        required=True,
    )
    parser.add_argument(
        "--metadata-output",
        required=True,
    )
    parser.add_argument(
        "--defaults-json",
        default="{}",
        help="JSON object containing default mitogenome metadata.",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "symlink"],
        default="copy",
    )
    parser.add_argument(
        "--log-file",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    """Run mitogenome submission preparation."""
    args = parse_args()
    logger = make_logger(
        name="mitogenome_submission",
        log_file_path=args.log_file,
    )

    try:
        defaults = json.loads(
            args.defaults_json
        )
        if not isinstance(defaults, dict):
            raise ValueError(
                "--defaults-json must decode to an object."
            )

        write_mitogenome_submission(
            runtime_manifest_path=Path(
                args.runtime_manifest
            ),
            job_directory=Path(
                args.job_directory
            ),
            output_directory=Path(
                args.output_directory
            ),
            metadata_output_path=Path(
                args.metadata_output
            ),
            defaults=defaults,
            mode=args.mode,
            logger=logger,
        )
        return 0

    except Exception as error:
        logger.exception(
            "Mitogenome submission preparation failed: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
