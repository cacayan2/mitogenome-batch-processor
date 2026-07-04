"""test_run_blast.py

Unit tests for the BLAST execution layer.
"""

# Imports
from pathlib import Path
from types import SimpleNamespace

from mitopipeline.exec import run_blast


class DummyLogger:
    """Minimal logger implementation for execution-layer tests."""

    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def exception(self, message):
        pass


def make_args(
    tmp_path: Path,
    **overrides,
) -> SimpleNamespace:
    """Create representative run_blast arguments."""
    arguments = {
        "sample_id": "sample_001",
        "query_fasta": str(
            tmp_path
            / "assembly"
            / "sample_001.fasta"
        ),
        "database": str(
            tmp_path
            / "resources"
            / "blast"
            / "fish_mito"
        ),
        "mode": "local",
        "output_dir": str(
            tmp_path
            / "phylogeny"
            / "blast"
        ),
        "working_dir": str(tmp_path),
        "threads": 4,
        "log_file": str(
            tmp_path
            / "logs"
            / "blast.log"
        ),
        "task": "blastn",
        "output_format": "6 qseqid sseqid",
        "evalue": 1e-5,
        "max_target_seqs": 50,
        "max_hsps": 1,
        "perc_identity": None,
        "query_coverage": None,
        "word_size": None,
    }

    arguments.update(overrides)

    return SimpleNamespace(**arguments)


def test_build_logger_uses_blast_logger_name(tmp_path, monkeypatch):
    """Test build_logger constructs the expected logger."""
    args = make_args(tmp_path)
    captured = {}

    def fake_make_logger(name, log_file_path):
        captured["name"] = name
        captured["log_file_path"] = log_file_path
        return DummyLogger()

    monkeypatch.setattr(
        run_blast,
        "make_logger",
        fake_make_logger,
    )

    logger = run_blast.build_logger(args)

    assert isinstance(logger, DummyLogger)
    assert captured["name"] == "blast"
    assert captured["log_file_path"] == args.log_file


def test_main_returns_zero_when_blast_succeeds(tmp_path, monkeypatch):
    """Test main returns zero after successful BLAST execution."""
    args = make_args(tmp_path)

    monkeypatch.setattr(
        run_blast,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        run_blast,
        "build_logger",
        lambda parsed_args: DummyLogger(),
    )

    class FakeBlastRunner:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def run(self):
            return SimpleNamespace(
                success=True,
                return_code=0,
                stdout="",
                stderr="",
                runtime_seconds=1.25,
            )

    monkeypatch.setattr(
        run_blast,
        "BlastRunner",
        FakeBlastRunner,
    )

    assert run_blast.main() == 0


def test_main_passes_arguments_to_blast_runner(tmp_path, monkeypatch):
    """Test main passes parsed values to BlastRunner."""
    args = make_args(tmp_path)
    captured = {}

    monkeypatch.setattr(
        run_blast,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        run_blast,
        "build_logger",
        lambda parsed_args: DummyLogger(),
    )

    class FakeBlastRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def run(self):
            return SimpleNamespace(
                success=True,
                return_code=0,
                stdout="",
                stderr="",
                runtime_seconds=1.0,
            )

    monkeypatch.setattr(
        run_blast,
        "BlastRunner",
        FakeBlastRunner,
    )

    result = run_blast.main()

    assert result == 0
    assert captured["query_fasta"] == Path(args.query_fasta)
    assert captured["database"] == args.database
    assert captured["output_dir"] == Path(args.output_dir)
    assert captured["working_dir"] == Path(args.working_dir)
    assert captured["sample_id"] == "sample_001"
    assert captured["threads"] == 4
    assert captured["task"] == "blastn"
    assert captured["max_target_seqs"] == 50
    assert captured["max_hsps"] == 1


def test_main_returns_blast_return_code_on_failure(
    tmp_path,
    monkeypatch,
):
    """Test main returns the external tool return code on failure."""
    args = make_args(tmp_path)

    monkeypatch.setattr(
        run_blast,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        run_blast,
        "build_logger",
        lambda parsed_args: DummyLogger(),
    )

    class FakeBlastRunner:
        def __init__(self, **kwargs):
            pass

        def run(self):
            return SimpleNamespace(
                success=False,
                return_code=2,
                stdout="",
                stderr="BLAST failed",
                runtime_seconds=0.1,
            )

    monkeypatch.setattr(
        run_blast,
        "BlastRunner",
        FakeBlastRunner,
    )

    assert run_blast.main() == 2


def test_main_returns_one_when_failure_has_zero_return_code(
    tmp_path,
    monkeypatch,
):
    """Test main converts an inconsistent failed result to exit code one."""
    args = make_args(tmp_path)

    monkeypatch.setattr(
        run_blast,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        run_blast,
        "build_logger",
        lambda parsed_args: DummyLogger(),
    )

    class FakeBlastRunner:
        def __init__(self, **kwargs):
            pass

        def run(self):
            return SimpleNamespace(
                success=False,
                return_code=0,
                stdout="",
                stderr="",
                runtime_seconds=0.1,
            )

    monkeypatch.setattr(
        run_blast,
        "BlastRunner",
        FakeBlastRunner,
    )

    assert run_blast.main() == 1


def test_main_returns_one_when_runner_raises(tmp_path, monkeypatch):
    """Test main returns one when runner construction or execution fails."""
    args = make_args(tmp_path)

    monkeypatch.setattr(
        run_blast,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        run_blast,
        "build_logger",
        lambda parsed_args: DummyLogger(),
    )

    class FakeBlastRunner:
        def __init__(self, **kwargs):
            raise RuntimeError("test failure")

    monkeypatch.setattr(
        run_blast,
        "BlastRunner",
        FakeBlastRunner,
    )

    assert run_blast.main() == 1