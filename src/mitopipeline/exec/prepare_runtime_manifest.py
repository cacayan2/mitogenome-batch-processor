"""prepare_runtime_manifest.py

Execution layer for runtime-manifest preparation.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.config.runtime_manifest import (
    prepare_runtime_manifest,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Create a normalized runtime manifest from a required "
            "FASTQ directory and an optional metadata manifest."
        )
    )

    parser.add_argument(
        "--input-directory",
        required=True,
    )

    parser.add_argument(
        "--manifest",
        default=None,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    parser.add_argument(
        "--skip-file-validation",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    """Prepare a runtime manifest."""
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="runtime_manifest",
            log_file_path=args.log_file,
        )

        table = prepare_runtime_manifest(
            output_path=Path(
                args.output
            ),
            source_manifest=args.manifest,
            input_directory=args.input_directory,
            validate_files=(
                not args.skip_file_validation
            ),
            logger=logger,
        )

        logger.info(
            f"Prepared runtime manifest containing "
            f"{len(table)} samples."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Runtime-manifest preparation failed: "
                f"{error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
