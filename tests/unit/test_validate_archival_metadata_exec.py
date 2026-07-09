"""test_validate_archival_metadata_exec.py

Unit tests for archival metadata validation CLI.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    validate_archival_metadata as archival_exec,
)


class FakeLogger:
    """Minimal logger for execution tests."""

    def info(
            self,
            message,
    ):
        """Accept info messages."""

    def exception(
            self,
            message,
    ):
        """Accept exception messages."""


def test_main_write_example(
        monkeypatch,
        tmp_path,
):
    """Confirm example-writing mode returns zero."""
    arguments = Namespace(
        metadata=None,
        write_example=str(
            tmp_path
            / "archival_metadata.tsv"
        ),
        log_file=str(
            tmp_path
            / "archival.log"
        ),
    )

    calls = {}

    monkeypatch.setattr(
        archival_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        archival_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    def fake_write_example_archival_metadata(
            output_path,
    ):
        calls["output_path"] = output_path

        return output_path

    monkeypatch.setattr(
        archival_exec,
        "write_example_archival_metadata",
        fake_write_example_archival_metadata,
    )

    assert archival_exec.main() == 0
    assert calls["output_path"].name == "archival_metadata.tsv"


def test_main_validation_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm invalid metadata returns one."""
    arguments = Namespace(
        metadata=str(
            tmp_path
            / "archival_metadata.tsv"
        ),
        write_example=None,
        log_file=str(
            tmp_path
            / "archival.log"
        ),
    )

    class FakeResult:
        """Fake failed validation result."""

        valid = False

    monkeypatch.setattr(
        archival_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        archival_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        archival_exec,
        "validate_archival_metadata_file",
        lambda archival_metadata_path, logger: FakeResult(),
    )

    assert archival_exec.main() == 1
