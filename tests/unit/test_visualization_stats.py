"""test_visualization_stats.py

Unit tests for circular genome visualization parsing.
"""

# Imports
from pathlib import Path

import pytest

from mitopipeline.stats.visualization_stats import (
    build_circular_map_data,
    parse_gff_attributes,
    parse_visualization_gff,
    read_visualization_fasta,
    validate_visualization_outputs,
)


def write_visualization_fixture(
        tmp_path: Path,
) -> tuple[Path, Path]:
    """Create small GFF and FASTA fixtures."""
    gff_path = (
        tmp_path
        / "result.gff"
    )

    fasta_path = (
        tmp_path
        / "result.fas"
    )

    fasta_path.write_text(
        ">mitogenome\n"
        + "ATGC" * 1000
        + "\n",
        encoding="utf-8",
    )

    gff_path.write_text(
        (
            "##gff-version 3\n"
            "mito\tMITOS2\tgene\t1\t300\t.\t+\t.\t"
            "ID=gene1;Name=cox1\n"
            "mito\tMITOS2\tCDS\t1\t300\t.\t+\t0\t"
            "ID=cds1;gene=cox1\n"
            "mito\tMITOS2\ttRNA\t500\t560\t.\t-\t.\t"
            "ID=trna1;Name=trnF\n"
            "mito\tMITOS2\trRNA\t700\t1000\t.\t+\t.\t"
            "ID=rrna1;Name=rrnL\n"
        ),
        encoding="utf-8",
    )

    return gff_path, fasta_path


def test_parse_gff_attributes():
    """Confirm GFF attributes are parsed."""
    result = parse_gff_attributes(
        "ID=gene1;Name=cox1;product=cytochrome oxidase"
    )

    assert result["ID"] == "gene1"
    assert result["Name"] == "cox1"


def test_parse_visualization_gff(
        tmp_path: Path,
):
    """Confirm drawable features are parsed."""
    gff_path, _ = write_visualization_fixture(
        tmp_path
    )

    features = parse_visualization_gff(
        gff_path
    )

    assert len(features) == 4
    assert features[0].label == "cox1"
    assert features[2].strand == "-"


def test_read_visualization_fasta(
        tmp_path: Path,
):
    """Confirm FASTA length and GC content are parsed."""
    _, fasta_path = write_visualization_fixture(
        tmp_path
    )

    sequence_id, genome_length, gc_content = read_visualization_fasta(
        fasta_path
    )

    assert sequence_id == "mitogenome"
    assert genome_length == 4000
    assert gc_content == 50.0


def test_build_circular_map_data(
        tmp_path: Path,
):
    """Confirm map data combines FASTA and GFF information."""
    gff_path, fasta_path = write_visualization_fixture(
        tmp_path
    )

    map_data = build_circular_map_data(
        sample_id="sample_001",
        gff_path=gff_path,
        fasta_path=fasta_path,
    )

    assert map_data.sample_id == "sample_001"
    assert map_data.genome_length == 4000
    assert len(map_data.features) == 4


def test_build_circular_map_data_out_of_bounds_raises(
        tmp_path: Path,
):
    """Confirm invalid feature coordinates are rejected."""
    fasta_path = (
        tmp_path
        / "result.fas"
    )

    gff_path = (
        tmp_path
        / "result.gff"
    )

    fasta_path.write_text(
        ">mitogenome\nATGC\n",
        encoding="utf-8",
    )

    gff_path.write_text(
        (
            "mito\tMITOS2\tgene\t1\t100\t.\t+\t.\t"
            "ID=gene1;Name=cox1\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="exceed",
    ):
        build_circular_map_data(
            sample_id="sample_001",
            gff_path=gff_path,
            fasta_path=fasta_path,
        )


def test_validate_visualization_outputs(
        tmp_path: Path,
):
    """Confirm non-empty output validation passes."""
    png_path = tmp_path / "map.png"
    svg_path = tmp_path / "map.svg"
    pdf_path = tmp_path / "map.pdf"

    for path in [
        png_path,
        svg_path,
        pdf_path,
    ]:
        path.write_bytes(
            b"not-empty"
        )

    validate_visualization_outputs(
        png_path=png_path,
        svg_path=svg_path,
        pdf_path=pdf_path,
    )
