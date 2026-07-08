"""generate_sample_report.py

Execution layer for per-sample Markdown reporting.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import (
    make_logger,
)
from mitopipeline.reporting.markdown_report import (
    write_sample_report,
)
from mitopipeline.reporting.report_data import (
    collect_sample_report_data,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate one Markdown report from existing "
            "MitoPipeline outputs."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
    )

    parser.add_argument(
        "--job-directory",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Generate one sample report."""
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="sample_report",
            log_file_path=args.log_file,
        )

        logger.info(
            f"Collecting report data for "
            f"{args.sample_id}."
        )

        report_data = collect_sample_report_data(
            sample_id=args.sample_id,
            job_directory=Path(
                args.job_directory
            ),
            logger=logger,
        )

        output_path = write_sample_report(
            report_data=report_data,
            output_path=Path(
                args.output
            ),
        )

        logger.info(
            f"Wrote sample report to "
            f"{output_path}."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Sample report generation failed: "
                f"{error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )