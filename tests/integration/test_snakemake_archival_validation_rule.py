"""Integration test for the archival validation Snakemake rule."""

from pathlib import Path


def test_archival_validation_rule_exists():
    """Archival validation rule declares expected outputs."""
    rule_path = Path(
        "ctrl/rules/archival_validation.smk"
    )
    text = rule_path.read_text(
        encoding="utf-8"
    )

    assert "rule archival_validation:" in text
    assert '"validation_summary.tsv"' in text
    assert '"validation_report.md"' in text
