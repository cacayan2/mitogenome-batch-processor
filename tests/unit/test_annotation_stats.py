"""test_annotation_stats.py

Unit tests for MITOS2 annotation statistics.
"""

# Imports
from pathlib import Path

from mitopipeline.stats.annotation_stats import (
    discover_annotation_gff,
    parse_annotation_stats,
    parse_gff_attributes,
)


def test_parse_gff_attributes():
    """Confirm GFF attributes are parsed."""
    attributes = parse_gff_attributes(
        "ID=gene1;Name=cox1;product=cytochrome oxidase"
    )

    assert attributes["ID"] == "gene1"
    assert attributes["Name"] == "cox1"
    assert (
        attributes["product"]
        == "cytochrome oxidase"
    )


def test_discover_annotation_gff(
        tmp_path: Path,
):
    """Confirm result.gff is discovered."""
    annotation_directory = (
        tmp_path
        / "annotation"
    )

    annotation_directory.mkdir()

    gff_path = (
        annotation_directory
        / "result.gff"
    )

    gff_path.touch()

    assert discover_annotation_gff(
        annotation_directory
    ) == gff_path


def test_parse_annotation_stats(
        tmp_path: Path,
):
    """Confirm feature counts and names are extracted."""
    annotation_directory = (
        tmp_path
        / "annotation"
    )

    annotation_directory.mkdir()

    (
        annotation_directory
        / "result.gff"
    ).write_text(
        (
            "##gff-version 3\n"
            "mito\tMITOS2\tgene\t1\t100\t.\t+\t.\t"
            "ID=gene1;Name=cox1\n"
            "mito\tMITOS2\tCDS\t1\t100\t.\t+\t0\t"
            "ID=cds1;gene=cox1\n"
            "mito\tMITOS2\ttRNA\t110\t180\t.\t+\t.\t"
            "ID=trna1;Name=trnF\n"
        ),
        encoding="utf-8",
    )

    stats = parse_annotation_stats(
        sample_id="sample_001",
        annotation_directory=annotation_directory,
    )

    assert stats.sample_id == "sample_001"
    assert stats.total_features == 3
    assert stats.feature_counts == {
        "CDS": 1,
        "gene": 1,
        "tRNA": 1,
    }
    assert "cox1" in stats.feature_names
    assert "trnF" in stats.feature_names