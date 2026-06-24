"""test_fastqc_stats.py

Unit tests for FastQC summary statistics parsing.
"""

# Imports
from pathlib import Path
import zipfile
import pytest

from mitopipeline.stats.fastqc_stats import (
    parse_fastqc_summary,
    calculate_overall_fastqc_status,
)


def create_fastqc_zip(zip_path: Path, summary_text: str) -> None:
    """Create a minimal FastQC zip fixture containing summary.txt."""

    # Creating parent directory.
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Creating minimal FastQC zip file.
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("sample_001_R1_fastqc/summary.txt", summary_text)


def test_parse_fastqc_summary_valid_zip(tmp_path):
    """Unit test confirming a valid FastQC summary zip parses correctly."""

    # Defining test paths.
    zip_path = tmp_path / "sample_001_R1_fastqc.zip"

    # Defining summary text.
    summary_text = (
        "PASS\tBasic Statistics\tsample_001_R1.fastq.gz\n"
        "PASS\tPer base sequence quality\tsample_001_R1.fastq.gz\n"
        "FAIL\tPer sequence quality scores\tsample_001_R1.fastq.gz\n"
        "FAIL\tPer base sequence content\tsample_001_R1.fastq.gz\n"
        "WARN\tPer sequence GC content\tsample_001_R1.fastq.gz\n"
        "PASS\tPer base N content\tsample_001_R1.fastq.gz\n"
        "PASS\tSequence Length Distribution\tsample_001_R1.fastq.gz\n"
        "PASS\tSequence Duplication Levels\tsample_001_R1.fastq.gz\n"
        "FAIL\tOverrepresented sequences\tsample_001_R1.fastq.gz\n"
        "WARN\tAdapter Content\tsample_001_R1.fastq.gz\n"
    )

    # Creating FastQC zip fixture.
    create_fastqc_zip(zip_path, summary_text)

    # Parsing FastQC summary.
    stats = parse_fastqc_summary(
        zip_path=zip_path,
        sample_id="sample_001",
        qc_stage="raw",
        logger=None,
    )

    # Assert statements.
    assert stats["sample_id"] == "sample_001"
    assert stats["qc_stage"] == "raw"
    assert stats["source_file"] == "sample_001_R1.fastq.gz"
    assert stats["overall_status"] == "FAIL"

    assert stats["module_statuses"]["Basic Statistics"] == "PASS"
    assert stats["module_statuses"]["Per base sequence quality"] == "PASS"
    assert stats["module_statuses"]["Per sequence quality scores"] == "FAIL"
    assert stats["module_statuses"]["Per base sequence content"] == "FAIL"
    assert stats["module_statuses"]["Per sequence GC content"] == "WARN"
    assert stats["module_statuses"]["Per base N content"] == "PASS"
    assert stats["module_statuses"]["Sequence Length Distribution"] == "PASS"
    assert stats["module_statuses"]["Sequence Duplication Levels"] == "PASS"
    assert stats["module_statuses"]["Overrepresented sequences"] == "FAIL"
    assert stats["module_statuses"]["Adapter Content"] == "WARN"


def test_parse_fastqc_summary_missing_zip_raises_error():
    """Unit test confirming a missing FastQC zip raises FileNotFoundError."""

    # Defining missing path.
    zip_path = Path("tests/fixtures/fastqc/missing_fastqc.zip")

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        parse_fastqc_summary(
            zip_path=zip_path,
            sample_id="sample_001",
            qc_stage="raw",
            logger=None,
        )


def test_parse_fastqc_summary_malformed_zip_raises_error(tmp_path):
    """Unit test confirming malformed FastQC zip raises ValueError."""

    # Creating malformed zip path.
    zip_path = tmp_path / "malformed_fastqc.zip"
    zip_path.write_text("not a real zip file", encoding="utf-8")

    # Assert statements.
    with pytest.raises(ValueError):
        parse_fastqc_summary(
            zip_path=zip_path,
            sample_id="sample_001",
            qc_stage="raw",
            logger=None,
        )


def test_parse_fastqc_summary_missing_summary_raises_error(tmp_path):
    """Unit test confirming zip without summary.txt raises ValueError."""

    # Defining test paths.
    zip_path = tmp_path / "missing_summary_fastqc.zip"

    # Creating zip without summary.txt.
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("sample_001_R1_fastqc/fastqc_data.txt", "placeholder")

    # Assert statements.
    with pytest.raises(ValueError):
        parse_fastqc_summary(
            zip_path=zip_path,
            sample_id="sample_001",
            qc_stage="raw",
            logger=None,
        )


def test_parse_fastqc_summary_malformed_summary_raises_error(tmp_path):
    """Unit test confirming malformed summary.txt raises ValueError."""

    # Defining test paths.
    zip_path = tmp_path / "malformed_summary_fastqc.zip"

    # Creating malformed summary text.
    summary_text = "PASS\tBasic Statistics\n"

    # Creating FastQC zip fixture.
    create_fastqc_zip(zip_path, summary_text)

    # Assert statements.
    with pytest.raises(ValueError):
        parse_fastqc_summary(
            zip_path=zip_path,
            sample_id="sample_001",
            qc_stage="raw",
            logger=None,
        )


def test_calculate_overall_fastqc_status_pass():
    """Unit test confirming all PASS module statuses return PASS."""

    # Defining module statuses.
    module_statuses = {
        "Basic Statistics": "PASS",
        "Per base sequence quality": "PASS",
    }

    # Assert statements.
    assert calculate_overall_fastqc_status(module_statuses) == "PASS"


def test_calculate_overall_fastqc_status_warn():
    """Unit test confirming WARN without FAIL returns WARN."""

    # Defining module statuses.
    module_statuses = {
        "Basic Statistics": "PASS",
        "Adapter Content": "WARN",
    }

    # Assert statements.
    assert calculate_overall_fastqc_status(module_statuses) == "WARN"


def test_calculate_overall_fastqc_status_fail():
    """Unit test confirming any FAIL returns FAIL."""

    # Defining module statuses.
    module_statuses = {
        "Basic Statistics": "PASS",
        "Adapter Content": "WARN",
        "Overrepresented sequences": "FAIL",
    }

    # Assert statements.
    assert calculate_overall_fastqc_status(module_statuses) == "FAIL"