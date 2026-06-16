"""test_sample.py

Unit tests for the Sample model.
"""

# Imports
from pathlib import Path
import pytest
from dataclasses import FrozenInstanceError

from mitopipeline.models.sample import Sample


def test_sample_creation_minimal():
    """Unit test for creating a Sample object with only required fields."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path
    )

    # Assert statements.
    assert sample.sample_id == "sample_001"
    assert sample.r1 == r1_path
    assert sample.r2 == r2_path
    assert sample.species is None
    assert sample.condition is None


def test_sample_creation_with_species_and_condition():
    """Unit test for creating a Sample object with species and condition."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path,
        species="Lepomis macrochirus",
        condition="before_wga"
    )

    # Assert statements.
    assert sample.sample_id == "sample_001"
    assert sample.r1 == r1_path
    assert sample.r2 == r2_path
    assert sample.species == "Lepomis macrochirus"
    assert sample.condition == "before_wga"


def test_sample_has_species():
    """Unit test for Sample.has_species()."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample objects.
    sample_with_species = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path,
        species="Lepomis macrochirus"
    )

    sample_without_species = Sample(
        sample_id="sample_002",
        r1=r1_path,
        r2=r2_path
    )

    # Assert statements.
    assert sample_with_species.has_species() is True
    assert sample_without_species.has_species() is False


def test_sample_has_condition():
    """Unit test for Sample.has_condition()."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample objects.
    sample_with_condition = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path,
        condition="before_wga"
    )

    sample_without_condition = Sample(
        sample_id="sample_002",
        r1=r1_path,
        r2=r2_path
    )

    # Assert statements.
    assert sample_with_condition.has_condition() is True
    assert sample_without_condition.has_condition() is False


def test_sample_fastq_files():
    """Unit test for Sample.fastq_files()."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path
    )

    # Calling fastq_files().
    fastq_files = sample.fastq_files()

    # Assert statements.
    assert fastq_files == (r1_path, r2_path)
    assert fastq_files[0] == r1_path
    assert fastq_files[1] == r2_path


def test_sample_is_immutable():
    """Unit test for confirming Sample object is immutable."""

    # Creating fake FASTQ paths.
    r1_path = Path("sample_001_R1.fastq.gz")
    r2_path = Path("sample_001_R2.fastq.gz")

    # Creating Sample object.
    sample = Sample(
        sample_id="sample_001",
        r1=r1_path,
        r2=r2_path
    )

    # Assert that modifying the Sample raises an error.
    with pytest.raises(FrozenInstanceError):
        sample.sample_id = "sample_002"