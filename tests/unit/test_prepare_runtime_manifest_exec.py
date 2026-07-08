"""test_prepare_runtime_manifest_exec.py

Unit tests for runtime-manifest execution layer.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    prepare_runtime_manifest as manifest_exec,
)


class FakeLogger:
    """Minimal logger for execution-layer tests."""

    def info(
            self,
            message,
    ):
        """Accept informational log messages."""

    def exception(
            self,
            message,
    ):
        """Accept exception log messages."""


def test_main_success(
        monkeypatch,
        tmp_path,
):
    """Confirm successful manifest preparation returns zero."""
    arguments = Namespace(
        manifest=str(
            tmp_path
            / "samples.tsv"
        ),
        input_directory=str(
            tmp_path
            / "reads"
        ),
        output=str(
            tmp_path
            / "runtime_manifest.tsv"
        ),
        log_file=str(
            tmp_path
            / "manifest.log"
        ),
        skip_file_validation=False,
    )

    calls = {}

    monkeypatch.setattr(
        manifest_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        manifest_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    class FakeTable:
        """Minimal table used by the test."""

        def __len__(
                self,
        ):
            return 2

    def fake_prepare_runtime_manifest(
            **kwargs,
    ):
        calls["kwargs"] = kwargs

        return FakeTable()

    monkeypatch.setattr(
        manifest_exec,
        "prepare_runtime_manifest",
        fake_prepare_runtime_manifest,
    )

    assert manifest_exec.main() == 0

    assert calls["kwargs"]["source_manifest"] == (
        arguments.manifest
    )

    assert calls["kwargs"]["input_directory"] == (
        arguments.input_directory
    )


def test_main_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm failed manifest preparation returns one."""
    arguments = Namespace(
        manifest=None,
        input_directory=str(
            tmp_path
            / "reads"
        ),
        output=str(
            tmp_path
            / "runtime_manifest.tsv"
        ),
        log_file=str(
            tmp_path
            / "manifest.log"
        ),
        skip_file_validation=False,
    )

    monkeypatch.setattr(
        manifest_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        manifest_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    def fake_prepare_runtime_manifest(
            **kwargs,
    ):
        raise RuntimeError(
            "boom"
        )

    monkeypatch.setattr(
        manifest_exec,
        "prepare_runtime_manifest",
        fake_prepare_runtime_manifest,
    )

    assert manifest_exec.main() == 1
