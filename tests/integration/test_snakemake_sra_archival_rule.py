"""Integration test for the SRA archival Snakemake rule."""

from pathlib import Path


def test_sra_archival_rule_exists():
    """Archival rule declares the required output path."""
    rule_path = Path(
        "ctrl/rules/sra_archival.smk"
    )
    text = rule_path.read_text(
        encoding="utf-8"
    )

    assert "rule sra_metadata:" in text
    assert (
        '"submission"'
        in text
    )
    assert (
        '"sra_metadata.tsv"'
        in text
    )
