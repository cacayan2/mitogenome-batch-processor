"""CLI for the table2asn validation prototype."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.archival.table2asn_validation import (
    write_table2asn_validation_outputs,
)
from mitopipeline.logging.logger_factory import (
    make_logger,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate generated mitogenome archival packages with table2asn."
        )
    )
    parser.add_argument(
        "--mitogenome-metadata",
        required=True,
    )
    parser.add_argument(
        "--submission-template",
        required=True,
    )
    parser.add_argument(
        "--output-directory",
        required=True,
    )
    parser.add_argument(
        "--summary-tsv",
        required=True,
    )
    parser.add_argument(
        "--summary-markdown",
        required=True,
    )
    parser.add_argument(
        "--table2asn-bin",
        default="table2asn",
    )
    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Run table2asn validation."""
    args = parse_args()
    logger = make_logger(
        name="table2asn_validation",
        log_file_path=args.log_file,
    )

    try:
        write_table2asn_validation_outputs(
            mitogenome_metadata_path=Path(
                args.mitogenome_metadata
            ),
            submission_template=Path(
                args.submission_template
            ),
            output_directory=Path(
                args.output_directory
            ),
            summary_tsv_path=Path(
                args.summary_tsv
            ),
            summary_markdown_path=Path(
                args.summary_markdown
            ),
            executable=args.table2asn_bin,
            logger=logger,
        )
        return 0

    except Exception as error:
        logger.exception(
            "table2asn validation workflow failed: %s",
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
