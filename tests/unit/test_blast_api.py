"""test_blast_api.py

Unit tests for local and remote BLAST execution.
"""

# Imports
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.api.blast import BlastRunner, DEFAULT_OUTFMT


def write_file(
    path: Path,
    contents: str = "test\n",
) -> None:
    """Write a test file."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        contents,
        encoding="utf-8",
    )


def make_runner(
    tmp_path: Path,
    **overrides,
) -> BlastRunner:
    """Create representative BLAST runner."""
    query_fasta = (
        tmp_path
        / "assembly"
        / "sample_001.fasta"
    )

    write_file(
        query_fasta,
        ">sample_001\nATGCATGC\n",
    )

    arguments = {
        "query_fasta": query_fasta,
        "database": str(
            tmp_path
            / "resources"
            / "blast"
            / "fish_mito"
        ),
        "output_dir": (
            tmp_path
            / "phylogeny"
            / "blast"
        ),
        "working_dir": tmp_path,
        "sample_id": "sample_001",
        "mode": "local",
        "threads": 4,
        "task": "blastn",
        "output_format": DEFAULT_OUTFMT,
        "evalue": 1e-5,
        "max_target_seqs": 50,
        "max_hsps": 1,
        "perc_identity": None,
        "query_coverage": None,
        "word_size": None,
        "logger": None,
    }

    arguments.update(overrides)

    return BlastRunner(**arguments)


@pytest.fixture
def valid_database(monkeypatch):
    """Mock successful blastdbcmd validation."""
    monkeypatch.setattr(
        "mitopipeline.api.blast.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="Database information",
            stderr="",
        ),
    )


def test_runner_inherits_from_base_tool(tmp_path):
    """Test BlastRunner inherits BaseTool."""
    assert isinstance(
        make_runner(tmp_path),
        BaseTool,
    )


def test_local_validation_calls_blastdbcmd(
    tmp_path,
    monkeypatch,
):
    """Test local mode validates database with blastdbcmd."""
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "mitopipeline.api.blast.subprocess.run",
        fake_run,
    )

    runner = make_runner(tmp_path)
    runner.validate_inputs()

    assert captured["command"] == [
        "blastdbcmd",
        "-db",
        runner.database,
        "-dbtype",
        "nucl",
        "-info",
    ]


def test_remote_validation_skips_blastdbcmd(
    tmp_path,
    monkeypatch,
):
    """Test remote mode requires no local database."""
    def fail(*args, **kwargs):
        raise AssertionError(
            "blastdbcmd was called in remote mode."
        )

    monkeypatch.setattr(
        "mitopipeline.api.blast.subprocess.run",
        fail,
    )

    runner = make_runner(
        tmp_path,
        mode="remote",
        database="refseq_genomic",
        threads=1,
    )

    runner.validate_inputs()


def test_invalid_local_database_is_rejected(
    tmp_path,
    monkeypatch,
):
    """Test unreadable local database is rejected."""
    monkeypatch.setattr(
        "mitopipeline.api.blast.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="database not found",
        ),
    )

    with pytest.raises(
        FileNotFoundError,
        match="missing or invalid",
    ):
        make_runner(
            tmp_path
        ).validate_inputs()


def test_missing_query_is_rejected(
    tmp_path,
    valid_database,
):
    """Test missing query FASTA is rejected."""
    runner = make_runner(tmp_path)
    runner.query_fasta.unlink()

    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_empty_query_is_rejected(
    tmp_path,
    valid_database,
):
    """Test empty query FASTA is rejected."""
    runner = make_runner(tmp_path)
    runner.query_fasta.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_local_command_uses_threads(tmp_path):
    """Test local command uses -num_threads."""
    runner = make_runner(tmp_path)

    command = runner.build_command()

    assert "-remote" not in command
    assert command[
        command.index("-num_threads") + 1
    ] == "4"


def test_remote_command_uses_remote_flag(tmp_path):
    """Test remote command uses NCBI remote execution."""
    runner = make_runner(
        tmp_path,
        mode="remote",
        database="refseq_genomic",
        threads=1,
    )

    command = runner.build_command()

    assert "-remote" in command
    assert "-num_threads" not in command
    assert command[
        command.index("-db") + 1
    ] == "refseq_genomic"


def test_command_adds_optional_arguments(tmp_path):
    """Test optional filters are included."""
    runner = make_runner(
        tmp_path,
        perc_identity=90,
        query_coverage=80,
        word_size=28,
    )

    command = runner.build_command()

    assert command[
        command.index("-perc_identity") + 1
    ] == "90"

    assert command[
        command.index("-qcov_hsp_perc") + 1
    ] == "80"

    assert command[
        command.index("-word_size") + 1
    ] == "28"


def test_max_hsps_is_omitted_when_none(tmp_path):
    """Test null max_hsps omits the argument."""
    command = make_runner(
        tmp_path,
        max_hsps=None,
    ).build_command()

    assert "-max_hsps" not in command


def test_excessive_threads_are_rejected(
    tmp_path,
    valid_database,
):
    """Test thread count cannot exceed available CPUs."""
    available_cpus = os.cpu_count()

    if available_cpus is None:
        pytest.skip(
            "CPU count unavailable."
        )

    runner = make_runner(
        tmp_path,
        threads=available_cpus + 1,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()