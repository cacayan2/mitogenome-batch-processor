"""test_sample_summary_model.py

Unit tests for SampleSummary model.
"""

# Imports
from pathlib import Path

from mitopipeline.models.sample_summary import SampleSummary


def test_sample_summary_minimal_creation():
    """Test minimal SampleSummary creation."""
    # Creating summary.
    summary = SampleSummary(sample_id="sample_001")

    # Checking fields.
    assert summary.sample_id == "sample_001"
    assert summary.raw_read_count is None
    assert summary.cds_count is None
    assert summary.annotation_warnings is None


def test_sample_summary_to_dict_minimal():
    """Test SampleSummary.to_dict with minimal fields."""
    # Creating summary.
    summary = SampleSummary(sample_id="sample_001")

    # Converting to dictionary.
    data = summary.to_dict()

    # Checking values.
    assert data["sample_id"] == "sample_001"
    assert data["raw_read_count"] is None
    assert data["cds_count"] is None


def test_sample_summary_to_dict_converts_fasta_path_to_string():
    """Test SampleSummary.to_dict converts fasta_path to string."""
    # Creating summary.
    summary = SampleSummary(
        sample_id="sample_001",
        fasta_path=Path("outputs/test_job/assembly/sample_001.fasta"),
    )

    # Converting to dictionary.
    data = summary.to_dict()

    # Checking converted path.
    assert data["fasta_path"] == "outputs/test_job/assembly/sample_001.fasta"


def test_sample_summary_to_dict_joins_annotation_warnings():
    """Test SampleSummary.to_dict joins annotation warnings."""
    # Creating summary.
    summary = SampleSummary(
        sample_id="sample_001",
        annotation_warnings=[
            "duplicated:2x rrnL",
            "WARNING: low confidence annotation",
        ],
    )

    # Converting to dictionary.
    data = summary.to_dict()

    # Checking joined warnings.
    assert data["annotation_warnings"] == (
        "duplicated:2x rrnL; WARNING: low confidence annotation"
    )


def test_sample_summary_to_dict_preserves_numeric_values():
    """Test SampleSummary.to_dict preserves numeric metric values."""
    # Creating summary.
    summary = SampleSummary(
        sample_id="sample_001",
        raw_read_count=1000,
        trimmed_read_count=900,
        reads_retained_percent=90.0,
        total_length_bp=16581,
        gc_content_percent=43.21,
        cds_count=13,
        trna_count=22,
        rrna_count=2,
    )

    # Converting to dictionary.
    data = summary.to_dict()

    # Checking values.
    assert data["raw_read_count"] == 1000
    assert data["trimmed_read_count"] == 900
    assert data["reads_retained_percent"] == 90.0
    assert data["total_length_bp"] == 16581
    assert data["gc_content_percent"] == 43.21
    assert data["cds_count"] == 13
    assert data["trna_count"] == 22
    assert data["rrna_count"] == 2