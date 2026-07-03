"""test_run_summary.py

Unit tests for run-level summary table writing.
"""

# Imports
from pathlib import Path
import csv

from mitopipeline.models.sample_summary import SampleSummary
from mitopipeline.reporting.run_summary import (
    sample_summaries_to_rows,
    write_run_summary,
    write_run_summary_tsv,
    write_run_summary_csv,
)


def make_sample_summaries() -> list[SampleSummary]:
    """Create sample summary fixtures."""
    return [
        SampleSummary(
            sample_id="sample_001",
            raw_read_count=1000,
            trimmed_read_count=900,
            reads_retained_percent=90.0,
            fasta_path=Path("outputs/test_job/assembly/sample_001.fasta"),
            total_length_bp=16581,
            gc_content_percent=43.21,
            cds_count=13,
            trna_count=22,
            rrna_count=2,
            annotation_warnings=["duplicated:2x rrnL"],
        ),
        SampleSummary(
            sample_id="sample_002",
            raw_read_count=2000,
            trimmed_read_count=1800,
            reads_retained_percent=90.0,
            fasta_path=Path("outputs/test_job/assembly/sample_002.fasta"),
            total_length_bp=16579,
            gc_content_percent=42.88,
            cds_count=13,
            trna_count=22,
            rrna_count=2,
            annotation_warnings=None,
        ),
    ]


def test_sample_summaries_to_rows():
    """Test converting sample summaries to rows."""
    # Creating summaries.
    summaries = make_sample_summaries()

    # Converting to rows.
    rows = sample_summaries_to_rows(summaries)

    # Checking rows.
    assert len(rows) == 2
    assert rows[0]["sample_id"] == "sample_001"
    assert rows[0]["fasta_path"] == "outputs/test_job/assembly/sample_001.fasta"
    assert rows[0]["annotation_warnings"] == "duplicated:2x rrnL"
    assert rows[1]["sample_id"] == "sample_002"
    assert rows[1]["annotation_warnings"] is None


def test_write_run_summary_tsv_creates_file(tmp_path):
    """Test writing run summary TSV creates output file."""
    # Defining output path.
    output_path = tmp_path / "summary" / "run_summary.tsv"

    # Writing TSV.
    write_run_summary_tsv(
        sample_summaries=make_sample_summaries(),
        output_path=output_path,
    )

    # Checking output exists.
    assert output_path.exists()


def test_write_run_summary_tsv_contents(tmp_path):
    """Test writing run summary TSV contents."""
    # Defining output path.
    output_path = tmp_path / "summary" / "run_summary.tsv"

    # Writing TSV.
    write_run_summary_tsv(
        sample_summaries=make_sample_summaries(),
        output_path=output_path,
    )

    # Reading TSV.
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    # Checking rows.
    assert len(rows) == 2
    assert rows[0]["sample_id"] == "sample_001"
    assert rows[0]["raw_read_count"] == "1000"
    assert rows[0]["trimmed_read_count"] == "900"
    assert rows[0]["total_length_bp"] == "16581"
    assert rows[0]["annotation_warnings"] == "duplicated:2x rrnL"


def test_write_run_summary_csv_contents(tmp_path):
    """Test writing run summary CSV contents."""
    # Defining output path.
    output_path = tmp_path / "summary" / "run_summary.csv"

    # Writing CSV.
    write_run_summary_csv(
        sample_summaries=make_sample_summaries(),
        output_path=output_path,
    )

    # Reading CSV.
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=",")
        rows = list(reader)

    # Checking rows.
    assert len(rows) == 2
    assert rows[0]["sample_id"] == "sample_001"
    assert rows[1]["sample_id"] == "sample_002"


def test_write_run_summary_empty_summaries_writes_empty_file(tmp_path):
    """Test writing empty summary list writes empty file."""
    # Defining output path.
    output_path = tmp_path / "summary" / "run_summary.tsv"

    # Writing empty summary.
    write_run_summary_tsv(
        sample_summaries=[],
        output_path=output_path,
    )

    # Checking output.
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == ""


def test_write_run_summary_custom_delimiter(tmp_path):
    """Test write_run_summary supports custom delimiters."""
    # Defining output path.
    output_path = tmp_path / "summary" / "run_summary.psv"

    # Writing pipe-delimited file.
    write_run_summary(
        sample_summaries=make_sample_summaries(),
        output_path=output_path,
        delimiter="|",
    )

    # Reading text.
    text = output_path.read_text(encoding="utf-8")

    # Checking delimiter.
    assert "|" in text
    assert "\t" not in text


def test_write_run_summary_creates_parent_directory(tmp_path):
    """Test write_run_summary creates parent directory."""
    # Defining nested output path.
    output_path = tmp_path / "nested" / "summary" / "run_summary.tsv"

    # Checking parent does not exist.
    assert not output_path.parent.exists()

    # Writing summary.
    write_run_summary_tsv(
        sample_summaries=make_sample_summaries(),
        output_path=output_path,
    )

    # Checking parent exists.
    assert output_path.parent.exists()
    assert output_path.exists()