"""test_fastp_api.py

Unit tests for FastpRunner behavior.
"""

# Imports
from pathlib import Path
import shutil
import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.api.fastp import FastpRunner
from mitopipeline.models.sample import Sample


def test_fastp_runner_inherits_from_basetool():
    """Unit test confirming FastpRunner inherits from BaseTool."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Assert statements.
    assert isinstance(runner, BaseTool)

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_builds_expected_command():
    """Unit test confirming FastpRunner builds the expected fastp command."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert command == [
        "fastp",
        "--in1", str(sample.r1),
        "--in2", str(sample.r2),
        "--out1", str(output_dir / "sample_001_R1.trimmed.fastq.gz"),
        "--out2", str(output_dir / "sample_001_R2.trimmed.fastq.gz"),
        "--html", str(output_dir / "sample_001.fastp.html"),
        "--json", str(output_dir / "sample_001.fastp.json"),
        "--thread", "4",
    ]

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_builds_command_with_optional_arguments():
    """Unit test confirming optional fastp arguments are added."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating tool options.
    tool_options = {
        "qualified_quality_phred": 20,
        "length_required": 50,
        "trim_front1": 5,
        "trim_tail1": 3,
        "cut_front": True,
        "cut_tail": True,
        "cut_right": True,
        "detect_adapter_for_pe": True,
    }

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        tool_options=tool_options,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert "--qualified_quality_phred" in command
    assert "20" in command
    assert "--length_required" in command
    assert "50" in command
    assert "--trim_front1" in command
    assert "5" in command
    assert "--trim_tail1" in command
    assert "3" in command
    assert "--cut_front" in command
    assert "--cut_tail" in command
    assert "--cut_right" in command
    assert "--detect_adapter_for_pe" in command

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_validates_existing_inputs():
    """Unit test confirming valid FASTQ inputs pass validation."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Validating inputs.
    runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_missing_r1_raises_error():
    """Unit test confirming a missing R1 FASTQ raises an exception."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/missing_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_missing_r2_raises_error():
    """Unit test confirming a missing R2 FASTQ raises an exception."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/missing_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_invalid_threads_raises_error():
    """Unit test confirming invalid thread count raises an exception."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=0,
        logger=None,
    )

    # Assert statements.
    with pytest.raises(ValueError):
        runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_expected_outputs():
    """Unit test confirming expected fastp output paths are generated."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Obtaining expected outputs.
    expected_outputs = runner._expected_fastp_outputs()

    # Assert statements.
    assert output_dir / "sample_001_R1.trimmed.fastq.gz" in expected_outputs
    assert output_dir / "sample_001_R2.trimmed.fastq.gz" in expected_outputs
    assert output_dir / "sample_001.fastp.html" in expected_outputs
    assert output_dir / "sample_001.fastp.json" in expected_outputs

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_validate_outputs_passes():
    """Unit test confirming output validation succeeds when all outputs exist."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Creating expected output files.
    for output_file in runner._expected_fastp_outputs():
        output_file.touch()

    # Validating outputs.
    runner.validate_outputs()

    # Cleanup.
    shutil.rmtree(output_dir)


def test_fastp_runner_validate_outputs_fails():
    """Unit test confirming output validation fails when outputs are missing."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()

    # Cleanup.
    shutil.rmtree(output_dir)

def test_fastp_runner_adds_all_value_options():
    """Unit test confirming all value-based optional fastp arguments are added."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating tool options.
    tool_options = {
        "qualified_quality_phred": 20,
        "length_required": 50,
        "trim_front1": 5,
        "trim_tail1": 3,
        "trim_front2": 6,
        "trim_tail2": 4,
        "cut_window_size": 4,
        "cut_mean_quality": 20,
        "n_base_limit": 5,
        "unqualified_percent_limit": 40,
        "average_qual": 20,
        "report_title": "sample_001 fastp report",
        "adapter_sequence": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
        "adapter_sequence_r2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
        "adapter_fasta": "tests/fixtures/adapters/adapters.fa",
    }

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        tool_options=tool_options,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert "--qualified_quality_phred" in command
    assert "20" in command
    assert "--length_required" in command
    assert "50" in command
    assert "--trim_front1" in command
    assert "5" in command
    assert "--trim_tail1" in command
    assert "3" in command
    assert "--trim_front2" in command
    assert "6" in command
    assert "--trim_tail2" in command
    assert "4" in command
    assert "--cut_window_size" in command
    assert "--cut_mean_quality" in command
    assert "--n_base_limit" in command
    assert "--unqualified_percent_limit" in command
    assert "--average_qual" in command
    assert "--report_title" in command
    assert "sample_001 fastp report" in command
    assert "--adapter_sequence" in command
    assert "--adapter_sequence_r2" in command
    assert "--adapter_fasta" in command

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_adds_all_boolean_flags():
    """Unit test confirming all boolean optional fastp flags are added."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating tool options.
    tool_options = {
        "detect_adapter_for_pe": True,
        "cut_front": True,
        "cut_tail": True,
        "cut_right": True,
        "disable_quality_filtering": True,
        "disable_length_filtering": True,
        "trim_poly_g": True,
        "disable_trim_poly_g": True,
        "trim_poly_x": True,
    }

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        tool_options=tool_options,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert "--detect_adapter_for_pe" in command
    assert "--cut_front" in command
    assert "--cut_tail" in command
    assert "--cut_right" in command
    assert "--disable_quality_filtering" in command
    assert "--disable_length_filtering" in command
    assert "--trim_poly_g" in command
    assert "--disable_trim_poly_g" in command
    assert "--trim_poly_x" in command

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_does_not_add_none_value_options():
    """Unit test confirming None-valued optional fastp arguments are skipped."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating tool options.
    tool_options = {
        "qualified_quality_phred": None,
        "length_required": None,
        "trim_front1": None,
        "trim_tail1": None,
        "average_qual": None,
    }

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        tool_options=tool_options,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert "--qualified_quality_phred" not in command
    assert "--length_required" not in command
    assert "--trim_front1" not in command
    assert "--trim_tail1" not in command
    assert "--average_qual" not in command

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastp_runner_does_not_add_false_boolean_flags():
    """Unit test confirming False-valued optional fastp flags are skipped."""

    # Creating temporary test directory.
    output_dir = Path("fastptest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating tool options.
    tool_options = {
        "detect_adapter_for_pe": False,
        "cut_front": False,
        "cut_tail": False,
        "cut_right": False,
        "disable_quality_filtering": False,
        "disable_length_filtering": False,
        "trim_poly_g": False,
        "disable_trim_poly_g": False,
        "trim_poly_x": False,
    }

    # Creating FastpRunner object.
    runner = FastpRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        threads=4,
        tool_options=tool_options,
        logger=None,
    )

    # Building fastp command.
    command = runner.build_command()

    # Assert statements.
    assert "--detect_adapter_for_pe" not in command
    assert "--cut_front" not in command
    assert "--cut_tail" not in command
    assert "--cut_right" not in command
    assert "--disable_quality_filtering" not in command
    assert "--disable_length_filtering" not in command
    assert "--trim_poly_g" not in command
    assert "--disable_trim_poly_g" not in command
    assert "--trim_poly_x" not in command

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)