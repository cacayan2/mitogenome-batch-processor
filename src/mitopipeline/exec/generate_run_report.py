"""generate_run_report.py

Execution layer for run-level Markdown reporting.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.reporting.run_markdown_report import write_run_report
from mitopipeline.reporting.run_report_data import collect_run_report_data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a run-level MitoPipeline Markdown report."
    )
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--job-directory", required=True)
    parser.add_argument("--enabled-stages", nargs="*", default=[])
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def main() -> int:
    """Generate the run-level report."""
    logger = None
    try:
        args = parse_args()
        logger = make_logger(
            name="run_report",
            log_file_path=args.log_file,
        )
        logger.info(f"Collecting run-level report data for {args.job_id}.")
        run_data = collect_run_report_data(
            job_id=args.job_id,
            job_directory=Path(args.job_directory),
            enabled_stages=args.enabled_stages,
            logger=logger,
        )
        output_path = write_run_report(
            run_data=run_data,
            output_path=Path(args.output),
        )
        logger.info(f"Wrote run-level report to {output_path}.")
        return 0
    except Exception as error:
        if logger is not None:
            logger.exception(f"Run-level report generation failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
