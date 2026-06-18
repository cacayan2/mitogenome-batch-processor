"""test_manifest_parser.py

Unit tests for sample manifest parsing behavior.
"""

from pathlib import Path
import pytest

from mitopipeline.manifest.sample_manifest import parse_sample_manifest


FIXTURE_DIR = Path("tests/fixtures")
MANIFEST_DIR = FIXTURE_DIR / "manifests"


def test_valid_minimal_manifest():
    """Unit test for parsing a valid minimal sample manifest."""

    manifest_path = MANIFEST_DIR / "valid_minimal.tsv"

    samples = parse_sample_manifest(manifest_path)

    assert len(samples) == 1
    assert samples[0].sample_id == "sample_001"
    assert samples[0].r1.exists()
    assert samples[0].r2.exists()
    assert samples[0].genus is None
    assert samples[0].species is None
    assert samples[0].source is None


def test_valid_manifest_with_taxonomy_and_source():
    """Unit test for parsing a manifest with genus, species, and source."""

    manifest_path = MANIFEST_DIR / "valid_with_taxonomy_source.tsv"

    samples = parse_sample_manifest(manifest_path)

    assert len(samples) == 2

    assert samples[0].sample_id == "sample_001"
    assert samples[0].genus == "Lepomis"
    assert samples[0].species == "macrochirus"
    assert samples[0].source == "museum"

    assert samples[1].sample_id == "sample_002"
    assert samples[1].genus == "Micropterus"
    assert samples[1].species == "salmoides"
    assert samples[1].source == "lab"


def test_blank_taxonomy_and_source_become_none():
    """Unit test for converting blank optional fields to None."""

    manifest_path = MANIFEST_DIR / "valid_blank_taxonomy_source.tsv"

    samples = parse_sample_manifest(manifest_path)

    assert len(samples) == 1
    assert samples[0].genus is None
    assert samples[0].species is None
    assert samples[0].source is None


def test_missing_required_column_raises_error():
    """Unit test for manifest missing a required column."""

    manifest_path = MANIFEST_DIR / "missing_r2_column.tsv"

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)


def test_empty_manifest_raises_error():
    """Unit test for a 0-byte empty manifest."""

    manifest_path = MANIFEST_DIR / "empty.tsv"

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)


def test_header_only_manifest_raises_error():
    """Unit test for a manifest with headers but no sample rows."""

    manifest_path = MANIFEST_DIR / "header_only.tsv"

    with pytest.raises(ValueError):
        parse_sample_manifest(manifest_path)


def test_missing_fastq_file_raises_error():
    """Unit test for manifest pointing to a missing FASTQ file."""

    manifest_path = MANIFEST_DIR / "missing_fastq_file.tsv"

    with pytest.raises(FileNotFoundError):
        parse_sample_manifest(manifest_path)


def test_missing_manifest_file_raises_error():
    """Unit test for a manifest path that does not exist."""

    manifest_path = MANIFEST_DIR / "does_not_exist.tsv"

    with pytest.raises(FileNotFoundError):
        parse_sample_manifest(manifest_path)