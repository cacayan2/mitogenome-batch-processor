"""Integration test for table2asn validation rule."""

from pathlib import Path


def test_table2asn_validation_rule_exists():
    """Rule declares prototype outputs."""
    rule_path = Path(
        "ctrl/rules/table2asn_validation.smk"
    )
    text = rule_path.read_text(
        encoding="utf-8"
    )

    assert "rule table2asn_validation:" in text
    assert '"validation_summary.tsv"' in text
    assert '"validation_summary.md"' in text
