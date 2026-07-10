"""pdf_export.py

Export Markdown reports to PDF using Pandoc with Typst as the PDF engine.
"""

# Imports
from dataclasses import dataclass
from pathlib import Path
import logging
import shutil
import subprocess


@dataclass(frozen=True)
class PdfExportResult:
    """Result of one Markdown-to-PDF export."""

    markdown_path: Path
    pdf_path: Path
    success: bool
    returncode: int
    stdout: str
    stderr: str


def resolve_executable(
        executable_name: str,
) -> str:
    """Resolve an executable name to a path.

    Args:
        executable_name (str): Executable name or path.

    Returns:
        str: Resolved executable path.

    Raises:
        FileNotFoundError: If the executable cannot be found.
    """
    executable_path = shutil.which(
        executable_name
    )

    if executable_path is None:
        raise FileNotFoundError(
            f"Required executable not found on PATH: "
            f"{executable_name}."
        )

    return executable_path


def validate_markdown_report(
        markdown_path: str | Path,
) -> Path:
    """Validate a Markdown report path.

    Args:
        markdown_path (str | Path): Markdown report path.

    Returns:
        Path: Resolved Markdown path.

    Raises:
        FileNotFoundError: If the Markdown file does not exist.
        ValueError: If the path is not a Markdown file.
    """
    markdown_path = Path(
        markdown_path
    ).expanduser().resolve()

    if not markdown_path.exists():
        raise FileNotFoundError(
            f"Markdown report not found: {markdown_path}."
        )

    if not markdown_path.is_file():
        raise ValueError(
            f"Markdown report path is not a file: "
            f"{markdown_path}."
        )

    if markdown_path.suffix.lower() not in {
        ".md",
        ".markdown",
    }:
        raise ValueError(
            f"Expected a Markdown report, found: "
            f"{markdown_path}."
        )

    return markdown_path


def default_pdf_path(
        markdown_path: str | Path,
) -> Path:
    """Return the default PDF path beside a Markdown report."""
    markdown_path = Path(
        markdown_path
    )

    return markdown_path.with_suffix(
        ".pdf"
    )


def build_resource_path(
        markdown_path: str | Path,
        job_directory: str | Path | None = None,
) -> str:
    """Build a Pandoc resource path for resolving linked images.

    Args:
        markdown_path (str | Path): Markdown report path.
        job_directory (str | Path | None): Optional pipeline job directory.

    Returns:
        str: Pandoc resource path string.
    """
    markdown_path = Path(
        markdown_path
    ).resolve()

    resource_paths = [
        markdown_path.parent,
    ]

    if job_directory is not None:
        job_directory = Path(
            job_directory
        ).resolve()

        resource_paths.append(
            job_directory
        )

    return ":".join(
        str(path)
        for path in resource_paths
    )


def build_pandoc_command(
        markdown_path: str | Path,
        pdf_path: str | Path,
        pandoc_bin: str = "pandoc",
        pdf_engine: str = "typst",
        job_directory: str | Path | None = None,
        standalone: bool = True,
) -> list[str]:
    """Build the Pandoc command for a Markdown-to-PDF export.

    Args:
        markdown_path (str | Path): Markdown input.
        pdf_path (str | Path): PDF output.
        pandoc_bin (str, optional): Pandoc executable. Defaults to
            "pandoc".
        pdf_engine (str, optional): PDF engine. Defaults to "typst".
        job_directory (str | Path | None, optional): Pipeline job
            directory used as a resource path.
        standalone (bool, optional): Whether to pass --standalone.

    Returns:
        list[str]: Command arguments.
    """
    command = [
        pandoc_bin,
        str(markdown_path),
        "--standalone",
        "--from",
        "gfm",
        "--to",
        "pdf",
        "--pdf-engine",
        pdf_engine,
        "--resource-path",
        build_resource_path(
            markdown_path=markdown_path,
            job_directory=job_directory,
        ),
        # Pass individual margins to prevent the Pandoc template bug
        "--variable", "margin-top=0.5in",
        "--variable", "margin-bottom=0.5in",
        "--variable", "margin-left=0.5in",
        "--variable", "margin-right=0.5in",
        "--output",
        str(pdf_path),
    ]

    if standalone:
        command.insert(
            2,
            "--standalone",
        )

    return command


def export_markdown_to_pdf(
        markdown_path: str | Path,
        pdf_path: str | Path | None = None,
        pandoc_bin: str = "pandoc",
        pdf_engine: str = "typst",
        job_directory: str | Path | None = None,
        logger: logging.Logger | None = None,
) -> PdfExportResult:
    """Export one Markdown report to PDF.

    The Markdown source is never modified. The final PDF is written through
    a temporary file and only replaces the destination after Pandoc succeeds.

    Args:
        markdown_path (str | Path): Markdown report input.
        pdf_path (str | Path | None, optional): PDF output. Defaults to
            the Markdown path with a `.pdf` suffix.
        pandoc_bin (str, optional): Pandoc executable. Defaults to
            "pandoc".
        pdf_engine (str, optional): PDF engine. Defaults to "typst".
        job_directory (str | Path | None, optional): Pipeline job
            directory for resolving linked images.
        logger (logging.Logger | None, optional): Logger.

    Returns:
        PdfExportResult: Export result.

    Raises:
        FileNotFoundError: If the input or required executables are absent.
        RuntimeError: If Pandoc fails.
    """
    markdown_path = validate_markdown_report(
        markdown_path
    )

    if pdf_path is None:
        pdf_path = default_pdf_path(
            markdown_path
        )

    pdf_path = Path(
        pdf_path
    ).expanduser().resolve()

    pdf_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pandoc_path = resolve_executable(
        pandoc_bin
    )

    # Validate the PDF engine explicitly for clearer errors.
    resolve_executable(
        pdf_engine
    )

    temporary_pdf_path = pdf_path.with_suffix(
        pdf_path.suffix + ".tmp"
    )

    temporary_pdf_path.unlink(
        missing_ok=True
    )

    command = build_pandoc_command(
        markdown_path=markdown_path,
        pdf_path=temporary_pdf_path,
        pandoc_bin=pandoc_path,
        pdf_engine=pdf_engine,
        job_directory=job_directory,
    )

    if logger is not None:
        logger.info(
            "Running PDF export command: "
            + " ".join(command)
        )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    export_result = PdfExportResult(
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        success=(
            result.returncode == 0
            and temporary_pdf_path.exists()
        ),
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

    if result.stdout and logger is not None:
        logger.info(
            result.stdout.strip()
        )

    if result.stderr and logger is not None:
        logger.warning(
            result.stderr.strip()
        )

    if not export_result.success:
        temporary_pdf_path.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            "PDF export failed for "
            f"{markdown_path}. Exit code: "
            f"{result.returncode}. stderr: "
            f"{result.stderr.strip()}"
        )

    temporary_pdf_path.replace(
        pdf_path
    )

    if logger is not None:
        logger.info(
            f"Wrote PDF report to {pdf_path}."
        )

    return export_result


def export_reports_to_pdf(
        markdown_paths: list[str | Path],
        pandoc_bin: str = "pandoc",
        pdf_engine: str = "typst",
        job_directory: str | Path | None = None,
        logger: logging.Logger | None = None,
) -> list[PdfExportResult]:
    """Export multiple Markdown reports to adjacent PDF files.

    Args:
        markdown_paths (list[str | Path]): Markdown reports.
        pandoc_bin (str, optional): Pandoc executable.
        pdf_engine (str, optional): PDF engine.
        job_directory (str | Path | None, optional): Job directory.
        logger (logging.Logger | None, optional): Logger.

    Returns:
        list[PdfExportResult]: Export results.

    Raises:
        RuntimeError: If one or more exports fail.
    """
    results: list[PdfExportResult] = []
    failures: list[str] = []

    for markdown_path in markdown_paths:
        try:
            results.append(
                export_markdown_to_pdf(
                    markdown_path=markdown_path,
                    pdf_path=None,
                    pandoc_bin=pandoc_bin,
                    pdf_engine=pdf_engine,
                    job_directory=job_directory,
                    logger=logger,
                )
            )

        except Exception as error:
            failures.append(
                f"{markdown_path}: {error}"
            )

            if logger is not None:
                logger.exception(
                    f"PDF export failed for {markdown_path}: "
                    f"{error}"
                )

    if failures:
        raise RuntimeError(
            "One or more PDF exports failed:\n- "
            + "\n- ".join(
                failures
            )
        )

    return results
