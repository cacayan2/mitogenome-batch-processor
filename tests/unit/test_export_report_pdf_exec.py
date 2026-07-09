"""test_export_report_pdf_exec.py

Unit tests for PDF export execution layer.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    export_report_pdf as pdf_exec,
)


class FakeLogger:
    """Minimal logger for execution tests."""

    def info(
            self,
            message,
    ):
        """Accept informational messages."""

    def exception(
            self,
            message,
    ):
        """Accept exception messages."""


def test_main_success(
        monkeypatch,
        tmp_path,
):
    """Confirm successful execution returns zero."""
    arguments = Namespace(
        markdown=str(
            tmp_path
            / "report.md"
        ),
        pdf=str(
            tmp_path
            / "report.pdf"
        ),
        job_directory=str(
            tmp_path
        ),
        pandoc_bin="pandoc",
        pdf_engine="typst",
        log_file=str(
            tmp_path
            / "pdf.log"
        ),
    )

    calls = {}

    monkeypatch.setattr(
        pdf_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        pdf_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    def fake_export_markdown_to_pdf(
            **kwargs,
    ):
        calls["kwargs"] = kwargs

    monkeypatch.setattr(
        pdf_exec,
        "export_markdown_to_pdf",
        fake_export_markdown_to_pdf,
    )

    assert pdf_exec.main() == 0
    assert calls["kwargs"]["pandoc_bin"] == "pandoc"
    assert calls["kwargs"]["pdf_engine"] == "typst"


def test_main_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm failures return one."""
    arguments = Namespace(
        markdown=str(
            tmp_path
            / "report.md"
        ),
        pdf=str(
            tmp_path
            / "report.pdf"
        ),
        job_directory=str(
            tmp_path
        ),
        pandoc_bin="pandoc",
        pdf_engine="typst",
        log_file=str(
            tmp_path
            / "pdf.log"
        ),
    )

    monkeypatch.setattr(
        pdf_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        pdf_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        pdf_exec,
        "export_markdown_to_pdf",
        lambda **kwargs: (
            _ for _ in ()
        ).throw(
            RuntimeError("boom")
        ),
    )

    assert pdf_exec.main() == 1
