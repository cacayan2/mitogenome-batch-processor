"""test_fastp_stats.py

Unit tests for fastp JSON statistics parsing.
"""

# Imports
from pathlib import Path
import json
import pytest

from mitopipeline.stats.fastp_stats import parse_fastp_json


def test_parse_fastp_json_valid_fixture():
    """Unit test confirming a valid fastp JSON fixture parses correctly."""

    # Defining fixture path.
    json_path = Path("tests/fixtures/fastp/sample_001.fastp.json")

    # Parsing fastp JSON.
    stats = parse_fastp_json(json_path=json_path, sample_id="sample_001")

    # Assert statements.
    assert stats["sample_id"] == "sample_001"

    assert stats["reads_in"] == 2
    assert stats["reads_out"] == 0
    assert stats["bases_in"] == 24
    assert stats["bases_out"] == 0

    assert stats["q20_rate_in"] == 1
    assert stats["q20_rate_out"] == 0
    assert stats["q30_rate_in"] == 1
    assert stats["q30_rate_out"] == 0

    assert stats["gc_content_in"] == 0.5
    assert stats["gc_content_out"] == 0

    assert stats["reads_removed"] == 2
    assert stats["bases_removed"] == 24
    assert stats["read_retention_rate"] == 0
    assert stats["base_retention_rate"] == 0

    assert stats["reads_passing_filtering"] == 0
    assert stats["low_qual_removed"] == 0
    assert stats["too_many_n_removed"] == 0
    assert stats["too_short_removed"] == 2
    assert stats["too_long_removed"] == 0

    assert stats["adapter_removed_reads"] == 0
    assert stats["adapter_removed_bases"] == 0


def test_parse_fastp_json_missing_file_raises_error():
    """Unit test confirming missing fastp JSON raises FileNotFoundError."""

    # Defining missing fixture path.
    json_path = Path("tests/fixtures/fastp/missing.fastp.json")

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        parse_fastp_json(json_path=json_path, sample_id="sample_001")


def test_parse_fastp_json_malformed_json_raises_error(tmp_path):
    """Unit test confirming malformed JSON raises JSONDecodeError."""

    # Creating malformed JSON file.
    json_path = tmp_path / "malformed.fastp.json"
    json_path.write_text("{bad json", encoding="utf-8")

    # Assert statements.
    with pytest.raises(json.JSONDecodeError):
        parse_fastp_json(json_path=json_path, sample_id="sample_001")


def test_parse_fastp_json_missing_required_section_raises_error(tmp_path):
    """Unit test confirming missing required JSON sections raise KeyError."""

    # Creating incomplete JSON file.
    json_path = tmp_path / "missing_summary.fastp.json"
    json_path.write_text(json.dumps({"filtering_result": {}}), encoding="utf-8")

    # Assert statements.
    with pytest.raises(KeyError):
        parse_fastp_json(json_path=json_path, sample_id="sample_001")