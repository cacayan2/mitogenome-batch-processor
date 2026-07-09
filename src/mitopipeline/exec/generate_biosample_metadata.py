"""Command-line execution layer for BioSample metadata generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mitopipeline.archival.biosample_metadata import (
    write_biosample_metadata,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a reviewable NCBI BioSample metadata TSV "
            "from the runtime sample manifest."
        )
    )
    parser.add_argument(
        "--runtime-manifest",
        required=True,
    )
    parser.add_argument(
        "--output",
        required=True,
    )
    parser.add_argument(
        "--defaults-json",
        default="{}",
        help="JSON object containing default BioSample fields.",
    )
    parser.add_argument(
        "--log-file",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    """Run BioSample metadata generation."""
    args = parse_args()
    logger = make_logger(
        name="biosample_metadata",
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

        write_biosample_metadata(
            runtime_manifest_path=Path(
                args.runtime_manifest
            ),
            output_path=Path(
                args.output
            ),
            defaults=defaults,
            logger=logger,
        )
        return 0

    except Exception as error:
        logger.exception(
            "BioSample metadata generation failed: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
