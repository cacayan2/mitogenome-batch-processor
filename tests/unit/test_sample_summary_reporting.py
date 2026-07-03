"""test_sample_summary_reporting.py

Unit tests for building per-sample summaries.
"""

# Imports
from pathlib import Path

from mitopipeline.models.assembly_stats import AssemblyStats
from mitopipeline.models.annotation_stats import AnnotationStats
from mitopipeline.reporting.sample_summary import (
    calculate_reads_retained_percent,
    build_sample_summary,
)


def make_assembly_stats() -> AssemblyStats:
    """Create AssemblyStats fixture."""
    return AssemblyStats(
        sample_id="sample_001",
        fasta_path=Path("outputs/test_job/assembly/sample_001.fasta"),
        contig_count=1,
        total_length_bp=16581,
        gc_content_percent=43.21,
        circularization_status="complete",
        runtime_seconds=120.5,
    )


def make_annotation_stats() -> AnnotationStats:
    """Create AnnotationStats fixture."""
    return AnnotationStats(
        sample_id="sample_001",
        cds_count=13,
        trna_count=22,
        rrna_count=2,
        gene_count=37,
        feature_count=99,
        warnings=["duplicated:2x rrnL"],
    )


def test_calculate_reads_retained_percent_valid_counts():
    """Test reads retained percent calculation."""
    # Calculating percent.
    percent = calculate_reads_retained_percent(
        raw_read_count=1000,
        trimmed_read_count=900,
    )

    # Checking result.
    assert percent == 90.0


def test_calculate_reads_retained_percent_rounds_to_two_decimals():
    """Test reads retained percent rounds to two decimals."""
    # Calculating percent.
    percent = calculate_reads_retained_percent(
        raw_read_count=3,
        trimmed_read_count=2,
    )

    # Checking result.
    assert percent == 66.67


def test_calculate_reads_retained_percent_missing_raw_returns_none():
    """Test missing raw read count returns None."""
    # Calculating percent.
    percent = calculate_reads_retained_percent(
        raw_read_count=None,
        trimmed_read_count=100,
    )

    # Checking result.
    assert percent is None


def test_calculate_reads_retained_percent_missing_trimmed_returns_none():
    """Test missing trimmed read count returns None."""
    # Calculating percent.
    percent = calculate_reads_retained_percent(
        raw_read_count=100,
        trimmed_read_count=None,
    )

    # Checking result.
    assert percent is None


def test_calculate_reads_retained_percent_zero_raw_returns_none():
    """Test zero raw read count returns None."""
    # Calculating percent.
    percent = calculate_reads_retained_percent(
        raw_read_count=0,
        trimmed_read_count=0,
    )

    # Checking result.
    assert percent is None


def test_build_sample_summary_with_all_stats():
    """Test build_sample_summary merges assembly and annotation stats."""
    # Creating fixtures.
    assembly_stats = make_assembly_stats()
    annotation_stats = make_annotation_stats()

    # Building summary.
    summary = build_sample_summary(
        sample_id="sample_001",
        assembly_stats=assembly_stats,
        annotation_stats=annotation_stats,
        raw_read_count=1000,
        trimmed_read_count=900,
    )

    # Checking QC/trimming fields.
    assert summary.sample_id == "sample_001"
    assert summary.raw_read_count == 1000
    assert summary.trimmed_read_count == 900
    assert summary.reads_retained_percent == 90.0

    # Checking assembly fields.
    assert summary.fasta_path == Path("outputs/test_job/assembly/sample_001.fasta")
    assert summary.contig_count == 1
    assert summary.total_length_bp == 16581
    assert summary.gc_content_percent == 43.21
    assert summary.circularization_status == "complete"
    assert summary.assembly_runtime_seconds == 120.5

    # Checking annotation fields.
    assert summary.cds_count == 13
    assert summary.trna_count == 22
    assert summary.rrna_count == 2
    assert summary.gene_count == 37
    assert summary.annotation_feature_count == 99
    assert summary.annotation_warnings == ["duplicated:2x rrnL"]


def test_build_sample_summary_without_optional_stats():
    """Test build_sample_summary handles missing stage stats."""
    # Building summary.
    summary = build_sample_summary(sample_id="sample_001")

    # Checking missing values.
    assert summary.sample_id == "sample_001"
    assert summary.fasta_path is None
    assert summary.contig_count is None
    assert summary.cds_count is None
    assert summary.trna_count is None
    assert summary.rrna_count is None
    assert summary.reads_retained_percent is None


def test_build_sample_summary_with_only_assembly_stats():
    """Test build_sample_summary handles assembly-only metrics."""
    # Building summary.
    summary = build_sample_summary(
        sample_id="sample_001",
        assembly_stats=make_assembly_stats(),
    )

    # Checking assembly populated.
    assert summary.total_length_bp == 16581
    assert summary.gc_content_percent == 43.21

    # Checking annotation missing.
    assert summary.cds_count is None
    assert summary.trna_count is None


def test_build_sample_summary_with_only_annotation_stats():
    """Test build_sample_summary handles annotation-only metrics."""
    # Building summary.
    summary = build_sample_summary(
        sample_id="sample_001",
        annotation_stats=make_annotation_stats(),
    )

    # Checking annotation populated.
    assert summary.cds_count == 13
    assert summary.trna_count == 22
    assert summary.rrna_count == 2

    # Checking assembly missing.
    assert summary.total_length_bp is None
    assert summary.gc_content_percent is None