"""test_generate_run_report.py

Unit tests for run-level report execution.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import generate_run_report as run_report_exec


class FakeLogger:
    """Minimal logger used in execution tests."""

    def info(self, message):
        """Accept informational messages."""

    def exception(self, message):
        """Accept exception messages."""


def test_main_success(monkeypatch, tmp_path):
    """Confirm successful execution returns zero."""
    arguments = Namespace(
        job_id="test_job",
        job_directory=str(tmp_path / "job"),
        enabled_stages=["trimming", "assembly"],
        output=str(tmp_path / "job" / "reporting" / "run_report.md"),
        log_file=str(tmp_path / "run_report.log"),
    )
    calls = {}
    monkeypatch.setattr(run_report_exec, "parse_args", lambda: arguments)
    monkeypatch.setattr(run_report_exec, "make_logger", lambda name, log_file_path: FakeLogger())
    monkeypatch.setattr(run_report_exec, "collect_run_report_data", lambda **kwargs: "run-data")

    def fake_write_run_report(run_data, output_path):
        calls["run_data"] = run_data
        calls["output_path"] = output_path
        return output_path

    monkeypatch.setattr(run_report_exec, "write_run_report", fake_write_run_report)
    assert run_report_exec.main() == 0
    assert calls["run_data"] == "run-data"


def test_main_failure(monkeypatch, tmp_path):
    """Confirm failed execution returns one."""
    arguments = Namespace(
        job_id="test_job",
        job_directory=str(tmp_path / "job"),
        enabled_stages=[],
        output=str(tmp_path / "run_report.md"),
        log_file=str(tmp_path / "run_report.log"),
    )
    monkeypatch.setattr(run_report_exec, "parse_args", lambda: arguments)
    monkeypatch.setattr(run_report_exec, "make_logger", lambda name, log_file_path: FakeLogger())
    monkeypatch.setattr(run_report_exec, "collect_run_report_data", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    assert run_report_exec.main() == 1
