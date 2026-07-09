"""Integration test for the BioSample archival Snakemake rule."""

from pathlib import Path


def test_biosample_archival_rule_exists():
    """Archival rule declares the required output path."""
    rule_path = Path(
        "ctrl/rules/biosample_archival.smk"
    )
    text = rule_path.read_text(
        encoding="utf-8"
    )

    assert "rule biosample_metadata:" in text
    assert '"biosample"' in text
    assert '"biosample_metadata.tsv"' in text
