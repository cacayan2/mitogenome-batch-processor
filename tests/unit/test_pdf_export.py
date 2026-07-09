"""test_pdf_export.py

Unit tests for Markdown-to-PDF export utilities.
"""

# Imports
from pathlib import Path
from types import SimpleNamespace

import pytest

from mitopipeline.reporting import pdf_export


class FakeLogger:
    """Minimal logger for PDF export tests."""

    def info(
            self,
            message,
    ):
        """Accept informational messages."""

    def warning(
            self,
            message,
    ):
        """Accept warning messages."""

    def exception(
            self,
            message,
    ):
        """Accept exception messages."""


def test_build_pandoc_command(
        tmp_path: Path,
):
    """Confirm Pandoc command is constructed correctly."""
    markdown_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    job_directory = tmp_path / "job"

    command = pdf_export.build_pandoc_command(
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        pandoc_bin="pandoc",
        pdf_engine="typst",
        job_directory=job_directory,
    )

    assert command[0] == "pandoc"
    assert "--pdf-engine" in command
    assert "typst" in command
    assert "--resource-path" in command
    assert str(pdf_path) in command


def test_validate_markdown_report_missing_raises(
        tmp_path: Path,
):
    """Confirm missing Markdown reports raise an error."""
    with pytest.raises(
            FileNotFoundError,
    ):
        pdf_export.validate_markdown_report(
            tmp_path
            / "missing.md"
        )


def test_export_markdown_to_pdf_success(
        tmp_path: Path,
        monkeypatch,
):
    """Confirm successful exports replace the destination PDF."""
    markdown_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"

    markdown_path.write_text(
        "# Report\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        pdf_export,
        "resolve_executable",
        lambda executable_name: f"/bin/{executable_name}",
    )

    def fake_run(
            command,
            capture_output,
            text,
            check,
    ):
        temporary_pdf_path = Path(
            command[
                command.index("--output")
                + 1
            ]
        )

        temporary_pdf_path.write_bytes(
            b"%PDF-1.7\n"
        )

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        pdf_export.subprocess,
        "run",
        fake_run,
    )

    result = pdf_export.export_markdown_to_pdf(
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        pandoc_bin="pandoc",
        pdf_engine="typst",
        job_directory=tmp_path,
        logger=FakeLogger(),
    )

    assert result.success is True
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(
        b"%PDF"
    )


def test_export_markdown_to_pdf_failure_preserves_existing_pdf(
        tmp_path: Path,
        monkeypatch,
):
    """Confirm failed exports do not destroy existing PDFs."""
    markdown_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"

    markdown_path.write_text(
        "# Report\n",
        encoding="utf-8",
    )

    pdf_path.write_bytes(
        b"existing pdf"
    )

    monkeypatch.setattr(
        pdf_export,
        "resolve_executable",
        lambda executable_name: f"/bin/{executable_name}",
    )

    def fake_run(
            command,
            capture_output,
            text,
            check,
    ):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="pandoc failed",
        )

    monkeypatch.setattr(
        pdf_export.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
            RuntimeError,
            match="PDF export failed",
    ):
        pdf_export.export_markdown_to_pdf(
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            pandoc_bin="pandoc",
            pdf_engine="typst",
            job_directory=tmp_path,
            logger=FakeLogger(),
        )

    assert pdf_path.read_bytes() == b"existing pdf"
