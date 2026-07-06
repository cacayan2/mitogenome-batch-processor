"""test_generate_alignment_dataset_exec.py

Unit tests for the alignment-dataset execution layer.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    generate_alignment_dataset as alignment_exec,
)


def test_main_success(
        monkeypatch,
        tmp_path,
):
    """Confirm the execution layer returns zero on success."""
    arguments = Namespace(
        sample_id="sample_001",
        assembly_fasta=str(
            tmp_path / "sample.fasta"
        ),
        top_hits=str(
            tmp_path / "sample.top_hits.tsv"
        ),
        output_fasta=str(
            tmp_path / "sample.phylogeny.fasta"
        ),
        entrez_email="test@example.com",
        entrez_api_key=None,
        log_file=str(
            tmp_path / "alignment.log"
        ),
    )

    calls = {}

    class FakeLogger:
        """Minimal logger used by the unit test."""

        def info(self, message):
            calls.setdefault(
                "info",
                [],
            ).append(message)

        def exception(self, message):
            calls.setdefault(
                "exception",
                [],
            ).append(message)

    def fake_generate_alignment_dataset(**kwargs):
        calls["arguments"] = kwargs

    monkeypatch.setattr(
        alignment_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        alignment_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        alignment_exec,
        "generate_alignment_dataset",
        fake_generate_alignment_dataset,
    )

    exit_code = alignment_exec.main()

    assert exit_code == 0

    assert calls["arguments"]["sample_id"] == (
        "sample_001"
    )

    assert calls["arguments"]["entrez_email"] == (
        "test@example.com"
    )


def test_main_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm the execution layer returns one on failure."""
    arguments = Namespace(
        sample_id="sample_001",
        assembly_fasta=str(
            tmp_path / "sample.fasta"
        ),
        top_hits=str(
            tmp_path / "sample.top_hits.tsv"
        ),
        output_fasta=str(
            tmp_path / "sample.phylogeny.fasta"
        ),
        entrez_email="test@example.com",
        entrez_api_key=None,
        log_file=str(
            tmp_path / "alignment.log"
        ),
    )

    calls = {}

    class FakeLogger:
        """Minimal logger used by the unit test."""

        def info(self, message):
            pass

        def exception(self, message):
            calls["exception"] = message

    def failing_generate_alignment_dataset(**kwargs):
        raise RuntimeError(
            "Test failure."
        )

    monkeypatch.setattr(
        alignment_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        alignment_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        alignment_exec,
        "generate_alignment_dataset",
        failing_generate_alignment_dataset,
    )

    exit_code = alignment_exec.main()

    assert exit_code == 1
    assert "Test failure" in calls["exception"]