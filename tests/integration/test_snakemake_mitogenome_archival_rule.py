"""Integration test for the mitogenome archival Snakemake rule."""

from pathlib import Path


def test_mitogenome_archival_rule_exists():
    """Archival rule declares the required output path."""
    rule_path = Path(
        "ctrl/rules/mitogenome_archival.smk"
    )
    text = rule_path.read_text(
        encoding="utf-8"
    )

    assert "rule mitogenome_submission:" in text
    assert '"mitogenomes"' in text
    assert '"mitogenome_metadata.tsv"' in text
