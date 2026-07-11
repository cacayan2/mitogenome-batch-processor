"""Execution layer for per-sample Markdown reporting."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.reporting.markdown_report import write_sample_report
from mitopipeline.reporting.report_data import collect_sample_report_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one Markdown report from pipeline outputs."
    )
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--job-directory", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def remove_duplicate_markdown_sections(
    report_text: str,
    headings: tuple[str, ...],
) -> str:
    """Remove repeated top-level report sections, keeping the first."""
    lines = report_text.splitlines()
    output: list[str] = []
    seen: set[str] = set()
    index = 0

    while index < len(lines):
        line = lines[index]

        if line in headings:
            if line in seen:
                index += 1
                while index < len(lines) and not lines[index].startswith("## "):
                    index += 1
                continue
            seen.add(line)

        output.append(line)
        index += 1

    return "\n".join(output).rstrip() + "\n"


def main() -> int:
    """Generate one sample report."""
    logger = None

    try:
        args = parse_args()
        logger = make_logger(
            name=f"sample_report.{args.sample_id}",
            log_file_path=args.log_file,
        )

        report_data = collect_sample_report_data(
            sample_id=args.sample_id,
            job_directory=Path(args.job_directory),
            logger=logger,
        )
        output_path = write_sample_report(
            report_data=report_data,
            output_path=Path(args.output),
        )

        report_text = output_path.read_text(encoding="utf-8")
        report_text = remove_duplicate_markdown_sections(
            report_text=report_text,
            headings=(
                "## Annotation",
                "## Closest BLAST matches",
            ),
        )
        output_path.write_text(report_text, encoding="utf-8")

        logger.info(
            "[%s] Wrote sample report to %s.",
            args.sample_id,
            output_path,
        )
        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                "Sample report generation failed: %s",
                error,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
