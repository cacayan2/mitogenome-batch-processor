"""test_manifest_parser.py

Unit tests for sample manifest parsing behavior.
"""

# Imports
from pathlib import Path
import shutil
from mitopipeline.manifest.sample_manifest import parse_sample_manifest
import pytest


def test_valid_minimal_manifest():
    """Unit test for parsing a valid minimal sample manifest."""

    # Creating temporary test directories.
    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"
    fastq_dir = test_dir / "fastq"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)
    fastq_dir.mkdir(parents=True)

    # Creating fake FASTQ files.
    (fastq_dir / "sample_001_R1.fastq.gz").touch()
    (fastq_dir / "sample_001_R2.fastq.gz").touch()

    # Creating valid manifest.
    manifest_path = manifest_dir / "valid_minimal.tsv"
    manifest_path.write_text(
        "sample_id\tr1\tr2\n"
        "sample_001\t../fastq/sample_001_R1.fastq.gz\t../fastq/sample_001_R2.fastq.gz\n"
    )

    # Parsing manifest.
    samples = parse_sample_manifest(manifest_path)

    # Assert statements.
    assert len(samples) == 1
    assert samples[0].sample_id == "sample_001"
    assert samples[0].r1.exists()
    assert samples[0].r2.exists()
    assert samples[0].species is None
    assert samples[0].condition is None

    shutil.rmtree(test_dir)


def test_valid_manifest_with_species_and_condition():
    """Unit test for parsing a manifest with species and condition."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"
    fastq_dir = test_dir / "fastq"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)
    fastq_dir.mkdir(parents=True)

    (fastq_dir / "sample_001_R1.fastq.gz").touch()
    (fastq_dir / "sample_001_R2.fastq.gz").touch()

    manifest_path = manifest_dir / "valid_with_species.tsv"
    manifest_path.write_text(
        "sample_id\tspecies\tr1\tr2\tcondition\n"
        "sample_001\tLepomis macrochirus\t../fastq/sample_001_R1.fastq.gz\t../fastq/sample_001_R2.fastq.gz\tbefore_wga\n"
    )

    samples = parse_sample_manifest(manifest_path)

    assert len(samples) == 1
    assert samples[0].sample_id == "sample_001"
    assert samples[0].species == "Lepomis macrochirus"
    assert samples[0].condition == "before_wga"

    shutil.rmtree(test_dir)


def test_blank_species_becomes_none():
    """Unit test for converting blank species values to None."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"
    fastq_dir = test_dir / "fastq"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)
    fastq_dir.mkdir(parents=True)

    (fastq_dir / "sample_001_R1.fastq.gz").touch()
    (fastq_dir / "sample_001_R2.fastq.gz").touch()

    manifest_path = manifest_dir / "blank_species.tsv"
    manifest_path.write_text(
        "sample_id\tspecies\tr1\tr2\tcondition\n"
        "sample_001\t\t../fastq/sample_001_R1.fastq.gz\t../fastq/sample_001_R2.fastq.gz\tbefore_wga\n"
    )

    samples = parse_sample_manifest(manifest_path)

    assert len(samples) == 1
    assert samples[0].species is None
    assert samples[0].condition == "before_wga"

    shutil.rmtree(test_dir)


def test_missing_required_column_raises_error():
    """Unit test for manifest missing a required column."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"
    fastq_dir = test_dir / "fastq"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)
    fastq_dir.mkdir(parents=True)

    (fastq_dir / "sample_001_R1.fastq.gz").touch()

    manifest_path = manifest_dir / "missing_r2_column.tsv"
    manifest_path.write_text(
        "sample_id\tr1\n"
        "sample_001\t../fastq/sample_001_R1.fastq.gz\n"
    )

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)

    shutil.rmtree(test_dir)


def test_empty_manifest_raises_error():
    """Unit test for a 0-byte empty manifest."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)

    manifest_path = manifest_dir / "empty.tsv"
    manifest_path.touch()

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)

    shutil.rmtree(test_dir)


def test_header_only_manifest_raises_error():
    """Unit test for a manifest with headers but no sample rows."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)

    manifest_path = manifest_dir / "header_only.tsv"
    manifest_path.write_text("sample_id\tr1\tr2\n")

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)

    shutil.rmtree(test_dir)


def test_missing_fastq_file_raises_error():
    """Unit test for manifest pointing to a missing FASTQ file."""

    test_dir = Path("manifesttest_tmp")
    manifest_dir = test_dir / "manifests"
    fastq_dir = test_dir / "fastq"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    manifest_dir.mkdir(parents=True)
    fastq_dir.mkdir(parents=True)

    (fastq_dir / "sample_001_R2.fastq.gz").touch()

    manifest_path = manifest_dir / "missing_fastq.tsv"
    manifest_path.write_text(
        "sample_id\tr1\tr2\n"
        "sample_001\t../fastq/missing_R1.fastq.gz\t../fastq/sample_001_R2.fastq.gz\n"
    )

    with pytest.raises(FileNotFoundError):
        parse_sample_manifest(manifest_path)

    shutil.rmtree(test_dir)


def test_missing_manifest_file_raises_error():
    """Unit test for a manifest path that does not exist."""

    manifest_path = Path("manifesttest_tmp/does_not_exist.tsv")

    if manifest_path.parent.exists():
        shutil.rmtree(manifest_path.parent)

    with pytest.raises(FileNotFoundError):
        parse_sample_manifest(manifest_path)