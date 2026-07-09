"""Unit tests for table2asn validation helpers."""

from pathlib import Path

from mitopipeline.archival.table2asn_validation import (
    parse_table2asn_messages,
    prepare_table2asn_input,
    render_table2asn_summary,
)

import pandas as pd


def test_prepare_table2asn_input(tmp_path: Path):
    """FASTA and feature table receive matching basenames."""
    fasta = tmp_path / "assembly.fasta"
    table = tmp_path / "result.tbl"

    fasta.write_text(
        ">old\nACGT\n",
        encoding="utf-8",
    )
    table.write_text(
        ">Feature old\n",
        encoding="utf-8",
    )

    output_fasta, output_table = prepare_table2asn_input(
        sample_id="sample_001",
        organism="Cyprinus carpio",
        assembly_fasta=fasta,
        feature_table=table,
        output_directory=tmp_path / "output",
    )

    assert output_fasta.name == "sample_001.fsa"
    assert output_table.name == "sample_001.tbl"
    assert "[organism=Cyprinus carpio]" in output_fasta.read_text(
        encoding="utf-8"
    )


def test_parse_table2asn_messages(tmp_path: Path):
    """Severity messages are counted."""
    validation = tmp_path / "sample.val"
    validation.write_text(
        "ERROR first\nWARNING second\nFATAL third\n",
        encoding="utf-8",
    )

    counts = parse_table2asn_messages(
        [validation]
    )

    assert counts["error"] == 1
    assert counts["warning"] == 1
    assert counts["fatal"] == 1


def test_render_table2asn_summary():
    """Summary report contains status counts."""
    table = pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "status": "PASS",
                "reject_count": 0,
                "fatal_count": 0,
                "error_count": 0,
                "warning_count": 1,
                "blockers": "",
            }
        ]
    )

    report = render_table2asn_summary(
        table
    )

    assert "Passed: 1" in report
    assert "sample_001" in report
