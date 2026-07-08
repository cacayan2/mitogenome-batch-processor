"""test_generate_sample_report.py

Unit tests for report-generation execution.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    generate_sample_report as report_exec,
)


class FakeLogger:
    """Minimal logger used in execution tests."""

    def info(self, message):
        """Accept informational messages."""

    def exception(self, message):
        """Accept exception messages."""


def test_main_success(
        monkeypatch,
        tmp_path,
):
    """Confirm successful execution returns zero."""
    arguments = Namespace(
        sample_id="sample_001",
        job_directory=str(
            tmp_path
            / "job"
        ),
        output=str(
            tmp_path
            / "job"
            / "reporting"
            / "sample_001.report.md"
        ),
        log_file=str(
            tmp_path
            / "report.log"
        ),
    )

    calls = {}

    monkeypatch.setattr(
        report_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        report_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        report_exec,
        "collect_sample_report_data",
        lambda **kwargs: "report-data",
    )

    def fake_write_sample_report(
            report_data,
            output_path,
    ):
        calls["report_data"] = report_data
        calls["output_path"] = output_path

        return output_path

    monkeypatch.setattr(
        report_exec,
        "write_sample_report",
        fake_write_sample_report,
    )

    assert report_exec.main() == 0
    assert calls["report_data"] == "report-data"


def test_main_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm failed execution returns one."""
    arguments = Namespace(
        sample_id="sample_001",
        job_directory=str(
            tmp_path
            / "job"
        ),
        output=str(
            tmp_path
            / "report.md"
        ),
        log_file=str(
            tmp_path
            / "report.log"
        ),
    )

    monkeypatch.setattr(
        report_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        report_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        report_exec,
        "collect_sample_report_data",
        lambda **kwargs: (
            _ for _ in ()
        ).throw(
            RuntimeError("boom")
        ),
    )

    assert report_exec.main() == 1