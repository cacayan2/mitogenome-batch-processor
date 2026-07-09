"""test_generate_circular_genome_map.py

Unit tests for circular genome map execution layer.
"""

# Imports
from argparse import Namespace

from mitopipeline.exec import (
    generate_circular_genome_map as map_exec,
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


def test_main_success(
        monkeypatch,
        tmp_path,
):
    """Confirm successful execution returns zero."""
    arguments = Namespace(
        sample_id="sample_001",
        gff=str(
            tmp_path
            / "result.gff"
        ),
        fasta=str(
            tmp_path
            / "result.fas"
        ),
        output_png=str(
            tmp_path
            / "map.png"
        ),
        output_svg=str(
            tmp_path
            / "map.svg"
        ),
        output_pdf=str(
            tmp_path
            / "map.pdf"
        ),
        dpi=600,
        log_file=str(
            tmp_path
            / "map.log"
        ),
    )

    calls = {}

    monkeypatch.setattr(
        map_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        map_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    def fake_render_circular_genome_map(
            **kwargs,
    ):
        calls["kwargs"] = kwargs

    monkeypatch.setattr(
        map_exec,
        "render_circular_genome_map",
        fake_render_circular_genome_map,
    )

    assert map_exec.main() == 0
    assert calls["kwargs"]["sample_id"] == "sample_001"
    assert calls["kwargs"]["dpi"] == 600


def test_main_failure(
        monkeypatch,
        tmp_path,
):
    """Confirm failed execution returns one."""
    arguments = Namespace(
        sample_id="sample_001",
        gff=str(
            tmp_path
            / "missing.gff"
        ),
        fasta=str(
            tmp_path
            / "missing.fas"
        ),
        output_png=str(
            tmp_path
            / "map.png"
        ),
        output_svg=str(
            tmp_path
            / "map.svg"
        ),
        output_pdf=str(
            tmp_path
            / "map.pdf"
        ),
        dpi=600,
        log_file=str(
            tmp_path
            / "map.log"
        ),
    )

    monkeypatch.setattr(
        map_exec,
        "parse_args",
        lambda: arguments,
    )

    monkeypatch.setattr(
        map_exec,
        "make_logger",
        lambda name, log_file_path: FakeLogger(),
    )

    monkeypatch.setattr(
        map_exec,
        "render_circular_genome_map",
        lambda **kwargs: (
            _ for _ in ()
        ).throw(
            RuntimeError("boom")
        ),
    )

    assert map_exec.main() == 1
