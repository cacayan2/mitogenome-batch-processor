"""test_blast_api.py

Unit tests for the BLAST API wrapper.
"""

# Imports
from pathlib import Path
import os

import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.api.blast import BlastRunner, DEFAULT_OUTFMT


def write_file(path: Path, contents: str = "test\n") -> None:
    """Write text to a file, creating parent directories as needed.

    Args:
        path (Path): File path.
        contents (str, optional): File contents. Defaults to "test\n".
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def make_blast_database(database_prefix: Path) -> None:
    """Create minimal nucleotide BLAST database component files.

    Args:
        database_prefix (Path): BLAST database prefix.
    """
    write_file(Path(f"{database_prefix}.nhr"))
    write_file(Path(f"{database_prefix}.nin"))
    write_file(Path(f"{database_prefix}.nsq"))


def make_runner(tmp_path: Path, **overrides) -> BlastRunner:
    """Create a valid BlastRunner for unit tests.

    Args:
        tmp_path (Path): Temporary pytest directory.
        **overrides: BlastRunner parameter overrides.

    Returns:
        BlastRunner: Configured runner.
    """
    query_fasta = tmp_path / "assembly" / "sample_001.fasta"
    database_prefix = tmp_path / "resources" / "blast" / "fish_mito"
    output_dir = tmp_path / "phylogeny" / "blast"

    write_file(
        query_fasta,
        ">sample_001\nATGCATGCATGC\n",
    )
    make_blast_database(database_prefix)

    arguments = {
        "query_fasta": query_fasta,
        "database": database_prefix,
        "output_dir": output_dir,
        "working_dir": tmp_path,
        "sample_id": "sample_001",
        "threads": 4,
        "task": "blastn",
        "output_format": DEFAULT_OUTFMT,
        "evalue": 1e-5,
        "max_target_seqs": 10,
        "max_hsps": 1,
        "perc_identity": None,
        "query_coverage": None,
        "word_size": None,
        "logger": None,
    }

    arguments.update(overrides)

    return BlastRunner(**arguments)


def test_blast_runner_inherits_from_base_tool(tmp_path):
    """Test BlastRunner inherits from BaseTool."""
    runner = make_runner(tmp_path)

    assert isinstance(runner, BaseTool)


def test_blast_runner_validate_inputs_accepts_valid_inputs(tmp_path):
    """Test validate_inputs accepts valid BLAST inputs."""
    runner = make_runner(tmp_path)

    runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_missing_query(tmp_path):
    """Test validate_inputs raises if query FASTA is missing."""
    runner = make_runner(tmp_path)
    runner.query_fasta.unlink()

    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_empty_query(tmp_path):
    """Test validate_inputs raises if query FASTA is empty."""
    runner = make_runner(tmp_path)
    runner.query_fasta.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_query_directory(tmp_path):
    """Test validate_inputs raises if query path is a directory."""
    runner = make_runner(tmp_path)
    runner.query_fasta.unlink()
    runner.query_fasta.mkdir()

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "extension",
    [
        ".nhr",
        ".nin",
        ".nsq",
    ],
)
def test_blast_runner_validate_inputs_raises_for_incomplete_database(
    tmp_path,
    extension,
):
    """Test validation raises if a required database component is absent."""
    runner = make_runner(tmp_path)
    Path(f"{runner.database}{extension}").unlink()

    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_empty_sample_id(tmp_path):
    """Test validate_inputs rejects an empty sample identifier."""
    runner = make_runner(tmp_path, sample_id="")

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "threads",
    [
        0,
        -1,
    ],
)
def test_blast_runner_validate_inputs_raises_for_invalid_threads(
    tmp_path,
    threads,
):
    """Test validate_inputs rejects non-positive thread counts."""
    runner = make_runner(tmp_path, threads=threads)

    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_excessive_threads(tmp_path):
    """Test validation rejects a thread count above available CPUs."""
    available_cpus = os.cpu_count()

    if available_cpus is None:
        pytest.skip("CPU count could not be determined.")

    runner = make_runner(
        tmp_path,
        threads=available_cpus + 1,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_blast_runner_validate_inputs_raises_for_invalid_task(tmp_path):
    """Test validate_inputs rejects unsupported blastn tasks."""
    runner = make_runner(
        tmp_path,
        task="invalid-task",
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "evalue",
    [
        0,
        -1,
    ],
)
def test_blast_runner_validate_inputs_raises_for_invalid_evalue(
    tmp_path,
    evalue,
):
    """Test validate_inputs rejects non-positive e-values."""
    runner = make_runner(
        tmp_path,
        evalue=evalue,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "max_target_seqs",
    [
        0,
        -1,
    ],
)
def test_blast_runner_validate_inputs_raises_for_invalid_max_targets(
    tmp_path,
    max_target_seqs,
):
    """Test validation rejects invalid maximum target counts."""
    runner = make_runner(
        tmp_path,
        max_target_seqs=max_target_seqs,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "identity",
    [
        -1,
        101,
    ],
)
def test_blast_runner_validate_inputs_raises_for_invalid_identity(
    tmp_path,
    identity,
):
    """Test validation rejects identity percentages outside 0-100."""
    runner = make_runner(
        tmp_path,
        perc_identity=identity,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


@pytest.mark.parametrize(
    "coverage",
    [
        -1,
        101,
    ],
)
def test_blast_runner_validate_inputs_raises_for_invalid_coverage(
    tmp_path,
    coverage,
):
    """Test validation rejects coverage percentages outside 0-100."""
    runner = make_runner(
        tmp_path,
        query_coverage=coverage,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_blast_runner_build_command_creates_output_directory(tmp_path):
    """Test build_command creates the BLAST output directory."""
    runner = make_runner(tmp_path)

    assert not runner.output_dir.exists()

    runner.build_command()

    assert runner.output_dir.exists()


def test_blast_runner_builds_expected_command(tmp_path):
    """Test BlastRunner builds the expected blastn command."""
    runner = make_runner(tmp_path)

    command = runner.build_command()

    assert command == [
        "blastn",
        "-query",
        str(runner.query_fasta),
        "-db",
        str(runner.database),
        "-out",
        str(runner.output_dir / "sample_001.blast.tsv"),
        "-outfmt",
        DEFAULT_OUTFMT,
        "-task",
        "blastn",
        "-evalue",
        "1e-05",
        "-max_target_seqs",
        "10",
        "-num_threads",
        "4",
        "-max_hsps",
        "1",
    ]


def test_blast_runner_build_command_adds_optional_arguments(tmp_path):
    """Test build_command adds selected optional BLAST arguments."""
    runner = make_runner(
        tmp_path,
        perc_identity=90.0,
        query_coverage=80.0,
        word_size=28,
    )

    command = runner.build_command()

    assert "-perc_identity" in command
    assert "90.0" in command

    assert "-qcov_hsp_perc" in command
    assert "80.0" in command

    assert "-word_size" in command
    assert "28" in command


def test_blast_runner_build_command_omits_max_hsps_when_none(tmp_path):
    """Test max_hsps is omitted when configured as None."""
    runner = make_runner(
        tmp_path,
        max_hsps=None,
    )

    command = runner.build_command()

    assert "-max_hsps" not in command


def test_blast_runner_expected_output_path(tmp_path):
    """Test the expected BLAST output path is deterministic."""
    runner = make_runner(tmp_path)

    assert runner._expected_blast_output() == (
        runner.output_dir / "sample_001.blast.tsv"
    )


def test_blast_runner_required_database_files(tmp_path):
    """Test required database component paths are generated."""
    runner = make_runner(tmp_path)

    assert runner._required_database_files() == [
        Path(f"{runner.database}.nhr"),
        Path(f"{runner.database}.nin"),
        Path(f"{runner.database}.nsq"),
    ]


def test_blast_runner_validate_outputs_accepts_nonempty_output(tmp_path):
    """Test validate_outputs accepts a populated BLAST result."""
    runner = make_runner(tmp_path)

    write_file(
        runner._expected_blast_output(),
        "sample_001\tNC_000001\t99.5\t16500\n",
    )

    runner.validate_outputs()


def test_blast_runner_validate_outputs_accepts_empty_output(tmp_path):
    """Test an empty output is accepted as a valid no-hit result."""
    runner = make_runner(tmp_path)

    write_file(
        runner._expected_blast_output(),
        "",
    )

    runner.validate_outputs()


def test_blast_runner_validate_outputs_raises_for_missing_output(tmp_path):
    """Test validate_outputs raises if the BLAST output is absent."""
    runner = make_runner(tmp_path)

    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()


def test_blast_runner_validate_outputs_raises_for_output_directory(tmp_path):
    """Test validate_outputs rejects a directory in place of output."""
    runner = make_runner(tmp_path)

    runner._expected_blast_output().mkdir(
        parents=True,
        exist_ok=True,
    )

    with pytest.raises(ValueError):
        runner.validate_outputs()