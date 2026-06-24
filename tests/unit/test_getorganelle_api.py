"""test_getorganelle_api.py

Unit tests for GetOrganelleRunner behavior.
"""

# Imports
from pathlib import Path
import shutil
import os
import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.api.getorganelle import GetOrganelleRunner
from mitopipeline.models.sample import Sample


def build_sample() -> Sample:
    """Create a reusable test Sample object."""

    return Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )


def cleanup_output_dir(output_dir: Path) -> None:
    """Remove test output directory if it exists."""

    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_getorganelle_runner_inherits_from_basetool():
    """Unit test confirming GetOrganelleRunner inherits from BaseTool."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    assert isinstance(runner, BaseTool)

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_builds_expected_base_command():
    """Unit test confirming GetOrganelleRunner builds the expected base command."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    sample = build_sample()

    runner = GetOrganelleRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    command = runner.build_command()

    assert command == [
        "get_organelle_from_reads.py",
        "-1", str(sample.r1),
        "-2", str(sample.r2),
        "-o", str(output_dir),
        "-F", "animal_mt",
        "-t", "4",
    ]

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_adds_value_options():
    """Unit test confirming value-based optional GetOrganelle arguments are added."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    tool_options = {
        "max_rounds": 10,
        "kmer": "21,45,65",
        "word_size": 15,
        "pre_grouping": 2,
        "max_reads": 100000,
        "target_coverage": 100,
        "min_read_length": 50,
        "max_read_length": 300,
        "expected_max_size": 20000,
        "expected_min_size": 15000,
        "seed_file": "tests/fixtures/seeds/fish_mt_seed.fasta",
        "genes_file": "tests/fixtures/seeds/fish_mt_genes.fasta",
        "exclude_fasta": "tests/fixtures/seeds/exclude.fasta",
        "prefix": "sample_001",
        "round_output_prefix": "round",
        "blast_path": "blastn",
        "bandage_path": "Bandage",
        "spades_path": "spades.py",
    }

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        tool_options=tool_options,
        threads=4,
        logger=None,
    )

    command = runner.build_command()

    assert "-R" in command
    assert "10" in command
    assert "-k" in command
    assert "21,45,65" in command
    assert "-w" in command
    assert "15" in command
    assert "-P" in command
    assert "2" in command
    assert "--max-reads" in command
    assert "100000" in command
    assert "--reduce-reads-for-coverage" in command
    assert "100" in command
    assert "--min-read-len" in command
    assert "50" in command
    assert "--max-read-len" in command
    assert "300" in command
    assert "--expected-max-size" in command
    assert "20000" in command
    assert "--expected-min-size" in command
    assert "15000" in command
    assert "-s" in command
    assert "tests/fixtures/seeds/fish_mt_seed.fasta" in command
    assert "--genes" in command
    assert "tests/fixtures/seeds/fish_mt_genes.fasta" in command
    assert "--exclude" in command
    assert "tests/fixtures/seeds/exclude.fasta" in command
    assert "--prefix" in command
    assert "sample_001" in command
    assert "--out-per-round" in command
    assert "round" in command
    assert "--which-blast" in command
    assert "blastn" in command
    assert "--which-bandage" in command
    assert "Bandage" in command
    assert "--which-spades" in command
    assert "spades.py" in command

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_adds_boolean_flags():
    """Unit test confirming boolean GetOrganelle flags are added."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    tool_options = {
        "overwrite": True,
        "continue_run": True,
        "fast_mode": True,
        "disentangle": True,
        "reverse_lsc": True,
        "no_slim": True,
        "keep_temp_files": True,
        "verbose": True,
    }

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        tool_options=tool_options,
        threads=4,
        logger=None,
    )

    command = runner.build_command()

    assert "--overwrite" in command
    assert "--continue" in command
    assert "--fast" in command
    assert "--disentangle" in command
    assert "--reverse-lsc" in command
    assert "--no-slim" in command
    assert "--keep-temp-files" in command
    assert "--verbose" in command

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_does_not_add_none_value_options():
    """Unit test confirming None-valued optional arguments are skipped."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    tool_options = {
        "max_rounds": None,
        "kmer": None,
        "seed_file": None,
    }

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        tool_options=tool_options,
        threads=4,
        logger=None,
    )

    command = runner.build_command()

    assert "-R" not in command
    assert "-k" not in command
    assert "-s" not in command

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_does_not_add_false_boolean_flags():
    """Unit test confirming False-valued boolean flags are skipped."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    tool_options = {
        "overwrite": False,
        "continue_run": False,
        "fast_mode": False,
        "verbose": False,
    }

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        tool_options=tool_options,
        threads=4,
        logger=None,
    )

    command = runner.build_command()

    assert "--overwrite" not in command
    assert "--continue" not in command
    assert "--fast" not in command
    assert "--verbose" not in command

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_validates_existing_inputs():
    """Unit test confirming valid inputs pass validation."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_missing_r1_raises_error():
    """Unit test confirming missing R1 raises FileNotFoundError."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/missing_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    runner = GetOrganelleRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_missing_r2_raises_error():
    """Unit test confirming missing R2 raises FileNotFoundError."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/missing_R2.fastq.gz"),
    )

    runner = GetOrganelleRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_invalid_threads_raises_error():
    """Unit test confirming invalid thread count raises ValueError."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=0,
        logger=None,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_threads_exceed_cpu_count_raises_error():
    """Unit test confirming too many threads raises ValueError."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=os.cpu_count() + 1,
        logger=None,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_invalid_organelle_type_raises_error():
    """Unit test confirming invalid organelle type raises ValueError."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="bad_type",
        threads=4,
        logger=None,
    )

    with pytest.raises(ValueError):
        runner.validate_inputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_expected_outputs():
    """Unit test confirming expected GetOrganelle output paths are generated."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    expected_outputs = runner._expected_getorganelle_outputs()

    assert output_dir / "sample_001.fasta" in expected_outputs
    assert output_dir / "sample_001.gfa" in expected_outputs

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_validate_outputs_passes():
    """Unit test confirming output validation passes when expected outputs exist."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)
    output_dir.mkdir(parents=True)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    for output_file in runner._expected_getorganelle_outputs():
        output_file.touch()

    runner.validate_outputs()

    cleanup_output_dir(output_dir)


def test_getorganelle_runner_validate_outputs_fails():
    """Unit test confirming output validation fails when expected outputs are missing."""

    output_dir = Path("getorganelletest_tmp")
    cleanup_output_dir(output_dir)
    output_dir.mkdir(parents=True)

    runner = GetOrganelleRunner(
        sample=build_sample(),
        output_dir=output_dir,
        working_dir=Path("."),
        organelle_type="animal_mt",
        threads=4,
        logger=None,
    )

    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()

    cleanup_output_dir(output_dir)