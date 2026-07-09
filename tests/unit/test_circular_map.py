"""test_circular_map.py

Unit tests for circular genome map rendering.
"""

# Imports
from pathlib import Path

from mitopipeline.stats.visualization_stats import (
    build_circular_map_data,
)
from mitopipeline.visualization.circular_map import (
    render_circular_map_data,
)


def write_visualization_fixture(
        tmp_path: Path,
) -> tuple[Path, Path]:
    """Create small map fixtures."""
    fasta_path = (
        tmp_path
        / "result.fas"
    )

    gff_path = (
        tmp_path
        / "result.gff"
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
            "mito\tMITOS2\ttRNA\t500\t560\t.\t-\t.\t"
            "ID=trna1;Name=trnF\n"
            "mito\tMITOS2\trRNA\t700\t1000\t.\t+\t.\t"
            "ID=rrna1;Name=rrnL\n"
        ),
        encoding="utf-8",
    )

    return gff_path, fasta_path


def test_render_circular_map_data(
        tmp_path: Path,
):
    """Confirm PNG, SVG, and PDF maps are produced."""
    gff_path, fasta_path = write_visualization_fixture(
        tmp_path
    )

    map_data = build_circular_map_data(
        sample_id="sample_001",
        gff_path=gff_path,
        fasta_path=fasta_path,
    )

    png_path = tmp_path / "map.png"
    svg_path = tmp_path / "map.svg"
    pdf_path = tmp_path / "map.pdf"

    render_circular_map_data(
        map_data=map_data,
        output_png=png_path,
        output_svg=svg_path,
        output_pdf=pdf_path,
        dpi=150,
    )

    assert png_path.exists()
    assert png_path.stat().st_size > 0

    assert svg_path.exists()
    assert svg_path.stat().st_size > 0

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
