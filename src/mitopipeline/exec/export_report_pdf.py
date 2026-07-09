"""export_report_pdf.py

Execution layer for exporting one Markdown report to PDF.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import (
    make_logger,
)
from mitopipeline.reporting.pdf_export import (
    export_markdown_to_pdf,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert one MitoPipeline Markdown report to PDF "
            "using Pandoc and Typst."
        )
    )

    parser.add_argument(
        "--markdown",
        required=True,
    )

    parser.add_argument(
        "--pdf",
        required=True,
    )

    parser.add_argument(
        "--job-directory",
        required=True,
    )

    parser.add_argument(
        "--pandoc-bin",
        default="pandoc",
    )

    parser.add_argument(
        "--pdf-engine",
        default="typst",
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Export one Markdown report to PDF."""
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="pdf_export",
            log_file_path=args.log_file,
        )

        export_markdown_to_pdf(
            markdown_path=Path(
                args.markdown
            ),
            pdf_path=Path(
                args.pdf
            ),
            pandoc_bin=args.pandoc_bin,
            pdf_engine=args.pdf_engine,
            job_directory=Path(
                args.job_directory
            ),
            logger=logger,
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"PDF export failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
