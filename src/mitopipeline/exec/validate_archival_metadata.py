"""validate_archival_metadata.py

Execution layer for archival metadata validation.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.config.archival_metadata import (
    validate_archival_metadata_file,
    write_example_archival_metadata,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate NCBI archival metadata TSV files."
        )
    )

    parser.add_argument(
        "--metadata",
        required=False,
    )

    parser.add_argument(
        "--write-example",
        required=False,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Validate archival metadata or write an example file."""
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="archival_metadata",
            log_file_path=args.log_file,
        )

        if args.write_example:
            output_path = write_example_archival_metadata(
                Path(
                    args.write_example
                )
            )

            logger.info(
                f"Wrote example archival metadata to "
                f"{output_path}."
            )

            return 0

        if not args.metadata:
            raise ValueError(
                "Either --metadata or --write-example is required."
            )

        result = validate_archival_metadata_file(
            archival_metadata_path=Path(
                args.metadata
            ),
            logger=logger,
        )

        if not result.valid:
            return 1

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Archival metadata validation failed: "
                f"{error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
