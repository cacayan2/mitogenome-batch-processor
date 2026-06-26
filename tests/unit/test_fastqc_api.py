"""test_fastqc_api.py

Unit tests for FastQCRunner behavior.
"""

# Imports
from pathlib import Path
import shutil
import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.api.fastqc import FastQCRunner
from mitopipeline.models.sample import Sample


def test_fastqc__runner_inherits_from_basetool():
    """Unit test confirming FastQCRunner inherits from BaseTool."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp.")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        threads = 8,
        working_dir=Path("."),
        logger=None,
    )

    # Assert statements.
    assert isinstance(runner, BaseTool)

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_builds_expected_command():
    """Unit test confirming FastQCRunner builds the expected FastQC command."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Building FastQC command.
    command = runner.build_command()

    # Assert statements.
    assert command == [
        "fastqc",
        "--threads",
        "4",
        str(sample.r1),
        str(sample.r2),
        "-o",
        str(output_dir),
    ]

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_validates_existing_inputs():
    """Unit test confirming valid FASTQ inputs pass validation."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Validating inputs.
    runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_missing_r1_raises_error():
    """Unit test confirming a missing R1 FASTQ raises an exception."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/missing_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_missing_r2_raises_error():
    """Unit test confirming a missing R2 FASTQ raises an exception."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/missing_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_expected_outputs():
    """Unit test confirming expected FastQC output paths are generated."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Obtaining expected outputs.
    expected_outputs = runner._expected_fastqc_outputs()

    # Assert statements.
    assert output_dir / "sample_001_R1_fastqc.html" in expected_outputs
    assert output_dir / "sample_001_R1_fastqc.zip" in expected_outputs
    assert output_dir / "sample_001_R2_fastqc.html" in expected_outputs
    assert output_dir / "sample_001_R2_fastqc.zip" in expected_outputs

    # Cleanup.
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fastqc_runner_validate_outputs_passes():
    """Unit test confirming output validation succeeds when all outputs exist."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Creating expected output files.
    for output_file in runner._expected_fastqc_outputs():
        output_file.touch()

    # Validating outputs.
    runner.validate_outputs()

    # Cleanup.
    shutil.rmtree(output_dir)


def test_fastqc_runner_validate_outputs_fails():
    """Unit test confirming output validation fails when outputs are missing."""

    # Creating temporary test directory.
    output_dir = Path("fastqtest_tmp")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)

    # Creating sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=Path("tests/fixtures/fastq/sample_001_R1.fastq.gz"),
        r2=Path("tests/fixtures/fastq/sample_001_R2.fastq.gz"),
    )

    # Creating FastQCRunner object.
    runner = FastQCRunner(
        sample=sample,
        output_dir=output_dir,
        working_dir=Path("."),
        logger=None,
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()

    # Cleanup.
    shutil.rmtree(output_dir)