"""test_phylogeny_stats.py

Unit tests for phylogenetic validation and rendering functions.
"""

# Imports
from pathlib import Path

import pytest
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from mitopipeline.stats.phylogeny_stats import (
    format_tree_label,
    parse_iqtree_model,
    read_phylogeny_dataset,
    render_phylogenetic_tree,
    validate_alignment,
    validate_newick_tree,
)


def make_phylogeny_records() -> list[SeqRecord]:
    """Create one assembly and six reference records."""
    return [
        SeqRecord(
            Seq("ATGC"),
            id="sample_001|assembled",
            description="",
        ),
        *[
            SeqRecord(
                Seq("ATGC"),
                id=(
                    f"reference_{rank:02d}"
                    f"|NC_00000{rank}.1"
                    f"|Species_{rank}"
                ),
                description="",
            )
            for rank in range(1, 7)
        ],
    ]


def test_read_phylogeny_dataset(
        tmp_path: Path,
):
    """Confirm one assembly and six references are accepted."""
    fasta_path = tmp_path / "dataset.fasta"

    SeqIO.write(
        make_phylogeny_records(),
        fasta_path,
        "fasta",
    )

    records = read_phylogeny_dataset(
        fasta_path
    )

    assert len(records) == 7
    assert records[0].id.endswith("|assembled")


def test_read_phylogeny_dataset_wrong_count_raises(
        tmp_path: Path,
):
    """Confirm an incomplete dataset raises an error."""
    fasta_path = tmp_path / "dataset.fasta"

    fasta_path.write_text(
        ">sample_001|assembled\nATGC\n",
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="Expected 7",
    ):
        read_phylogeny_dataset(
            fasta_path
        )


def test_validate_alignment(
        tmp_path: Path,
):
    """Confirm equal-length aligned sequences are accepted."""
    alignment_path = tmp_path / "aligned.fasta"

    records = make_phylogeny_records()

    for record in records:
        record.seq = Seq("ATGC--")

    SeqIO.write(
        records,
        alignment_path,
        "fasta",
    )

    parsed = validate_alignment(
        alignment_path
    )

    assert len(parsed) == 7
    assert len(parsed[0].seq) == 6


def test_validate_alignment_unequal_lengths_raises(
        tmp_path: Path,
):
    """Confirm unequal alignment lengths raise an error."""
    alignment_path = tmp_path / "aligned.fasta"

    records = make_phylogeny_records()
    records[0].seq = Seq("ATGC--")

    SeqIO.write(
        records,
        alignment_path,
        "fasta",
    )

    with pytest.raises(
            ValueError,
            match="equal lengths",
    ):
        validate_alignment(
            alignment_path
        )


def test_validate_newick_tree(
        tmp_path: Path,
):
    """Confirm a seven-tip Newick tree is accepted."""
    tree_path = tmp_path / "tree.nwk"

    tree_path.write_text(
        (
            "("
            "sample_001|assembled:0.1,"
            "reference_01|NC_000001.1|Species_1:0.1,"
            "reference_02|NC_000002.1|Species_2:0.1,"
            "reference_03|NC_000003.1|Species_3:0.1,"
            "reference_04|NC_000004.1|Species_4:0.1,"
            "reference_05|NC_000005.1|Species_5:0.1,"
            "reference_06|NC_000006.1|Species_6:0.1"
            ");"
        ),
        encoding="utf-8",
    )

    tree = validate_newick_tree(
        tree_path
    )

    assert len(tree.get_terminals()) == 7


def test_format_tree_label():
    """Confirm reference identifiers become readable labels."""
    label = format_tree_label(
        "reference_01|NC_012345.1|Etheostoma_blennioides"
    )

    assert label == (
        "Etheostoma blennioides [NC_012345.1]"
    )


def test_parse_iqtree_model(
        tmp_path: Path,
):
    """Confirm selected model is parsed from IQ-TREE report."""
    report_path = tmp_path / "sample.iqtree"

    report_path.write_text(
        "Best-fit model according to BIC: TIM2+F+I+G4\n",
        encoding="utf-8",
    )

    assert parse_iqtree_model(
        report_path
    ) == "TIM2+F+I+G4"


def test_render_phylogenetic_tree(
        tmp_path: Path,
):
    """Confirm SVG, PDF, and PNG figures are produced."""
    tree_path = tmp_path / "tree.nwk"
    svg_path = tmp_path / "tree.svg"
    pdf_path = tmp_path / "tree.pdf"
    png_path = tmp_path / "tree.png"

    tree_path.write_text(
        (
            "("
            "sample_001|assembled:0.1,"
            "reference_01|NC_000001.1|Species_1:0.1,"
            "reference_02|NC_000002.1|Species_2:0.1,"
            "reference_03|NC_000003.1|Species_3:0.1,"
            "reference_04|NC_000004.1|Species_4:0.1,"
            "reference_05|NC_000005.1|Species_5:0.1,"
            "reference_06|NC_000006.1|Species_6:0.1"
            ");"
        ),
        encoding="utf-8",
    )

    render_phylogenetic_tree(
        tree_path=tree_path,
        output_svg=svg_path,
        output_pdf=pdf_path,
        output_png=png_path,
        title="Test phylogeny",
        dpi=300,
    )

    assert svg_path.exists()
    assert svg_path.stat().st_size > 0

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    assert png_path.exists()
    assert png_path.stat().st_size > 0