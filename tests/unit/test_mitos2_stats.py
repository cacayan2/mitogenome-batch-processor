"""test_mitos2_stats.py

Unit tests for parsing MITOS2 annotation statistics.
"""

# Imports
from pathlib import Path
import pytest

from mitopipeline.models.annotation_stats import AnnotationStats
from mitopipeline.stats.mitos2_stats import (
    parse_gff_attributes,
    parse_mitos2_gff,
    parse_mitos2_warnings,
    parse_annotation_stats,
)


def write_file(path: Path, contents: str) -> None:
    """Write contents to a file, creating parent directories as needed.

    Args:
        path (Path): Output file path.
        contents (str): File contents.
    """
    # Creating parent directory.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Writing contents.
    path.write_text(contents, encoding="utf-8")


def make_mitos2_gff(tmp_path: Path) -> Path:
    """Create a small MITOS2-like GFF file.

    Args:
        tmp_path (Path): Temporary pytest directory.

    Returns:
        Path: Path to synthetic MITOS2 GFF.
    """
    # Defining GFF contents.
    contents = """##gff-version 3
3185-(circular)\tmitos\tregion\t1\t16581\t.\t+\t.\tID=region1;Is_circular=True;Name=3185-(circular)
3185-(circular)\tmitos\tgene\t813\t1787\t.\t+\t.\tID=gene_nad1;Name=nad1;gene_id=nad1
3185-(circular)\tmitos\texon\t813\t1787\t1011489320.5\t+\t0\tParent=transcript_nad1;Name=nad1
3185-(circular)\tmitfi\tncRNA_gene\t1792\t1863\t.\t+\t.\tID=gene_trnI;Name=trnI;gene_id=trnI
3185-(circular)\tmitfi\ttRNA\t1792\t1863\t.\t+\t.\tID=transcript_trnI(gat);Name=trnI(gat);Parent=gene_trnI(gat);gene_id=trnI(gat)
3185-(circular)\tmitfi\texon\t1792\t1863\t3.100000117717272e-11\t+\t.\tParent=transcript_trnI;Name=trnI
3185-(circular)\tmitfi\tncRNA_gene\t14611\t15563\t.\t+\t.\tID=gene_rrnS;Name=rrnS;gene_id=rrnS
3185-(circular)\tmitfi\trRNA\t14611\t15563\t.\t+\t.\tID=transcript_rrnS;Name=rrnS;Parent=gene_rrnS;gene_id=rrnS
3185-(circular)\tmitfi\texon\t14611\t15563\t0.0\t+\t.\tParent=transcript_rrnS;Name=rrnS
"""

    # Writing GFF file.
    gff_path = tmp_path / "result.gff"
    write_file(gff_path, contents)

    # Returning path.
    return gff_path


def make_full_mitos2_gff(tmp_path: Path) -> Path:
    """Create a fuller MITOS2-like GFF with canonical animal mitogenome counts.

    Args:
        tmp_path (Path): Temporary pytest directory.

    Returns:
        Path: Path to synthetic MITOS2 GFF.
    """
    # Protein-coding genes.
    protein_genes = [
        "nad1",
        "nad2",
        "cox1",
        "cox2",
        "atp8",
        "atp6",
        "cox3",
        "nad3",
        "nad4l",
        "nad4",
        "nad5",
        "nad6",
        "cob",
    ]

    # tRNA genes.
    trna_genes = [
        "trnL2",
        "trnI",
        "trnQ",
        "trnM",
        "trnW",
        "trnA",
        "trnN",
        "trnC",
        "trnY",
        "trnS2",
        "trnD",
        "trnK",
        "trnG",
        "trnR",
        "trnH",
        "trnS1",
        "trnL1",
        "trnE",
        "trnT",
        "trnP",
        "trnF",
        "trnV",
    ]

    # rRNA genes.
    rrna_genes = ["rrnS", "rrnL"]

    # Initializing lines.
    lines = [
        "##gff-version 3",
        "3185-(circular)\tmitos\tregion\t1\t16581\t.\t+\t.\tID=region1;Is_circular=True;Name=3185-(circular)",
    ]

    # Adding protein-coding gene rows.
    position = 1
    for gene in protein_genes:
        lines.append(
            f"3185-(circular)\tmitos\tgene\t{position}\t{position + 100}\t.\t+\t.\tID=gene_{gene};Name={gene};gene_id={gene}"
        )
        lines.append(
            f"3185-(circular)\tmitos\texon\t{position}\t{position + 100}\t100.0\t+\t0\tParent=transcript_{gene};Name={gene}"
        )
        position += 101

    # Adding tRNA rows.
    for gene in trna_genes:
        lines.append(
            f"3185-(circular)\tmitfi\tncRNA_gene\t{position}\t{position + 70}\t.\t+\t.\tID=gene_{gene};Name={gene};gene_id={gene}"
        )
        lines.append(
            f"3185-(circular)\tmitfi\ttRNA\t{position}\t{position + 70}\t.\t+\t.\tID=transcript_{gene};Name={gene};Parent=gene_{gene};gene_id={gene}"
        )
        lines.append(
            f"3185-(circular)\tmitfi\texon\t{position}\t{position + 70}\t0.0\t+\t.\tParent=transcript_{gene};Name={gene}"
        )
        position += 71

    # Adding rRNA rows.
    for gene in rrna_genes:
        lines.append(
            f"3185-(circular)\tmitfi\tncRNA_gene\t{position}\t{position + 900}\t.\t+\t.\tID=gene_{gene};Name={gene};gene_id={gene}"
        )
        lines.append(
            f"3185-(circular)\tmitfi\trRNA\t{position}\t{position + 900}\t.\t+\t.\tID=transcript_{gene};Name={gene};Parent=gene_{gene};gene_id={gene}"
        )
        lines.append(
            f"3185-(circular)\tmitfi\texon\t{position}\t{position + 900}\t0.0\t+\t.\tParent=transcript_{gene};Name={gene}"
        )
        position += 901

    # Writing GFF file.
    gff_path = tmp_path / "full_result.gff"
    write_file(gff_path, "\n".join(lines) + "\n")

    # Returning path.
    return gff_path


def test_parse_gff_attributes():
    """Test GFF attribute parsing."""
    # Parsing attributes.
    attributes = parse_gff_attributes("ID=gene_nad1;Name=nad1;gene_id=nad1")

    # Checking parsed values.
    assert attributes["ID"] == "gene_nad1"
    assert attributes["Name"] == "nad1"
    assert attributes["gene_id"] == "nad1"


def test_parse_gff_attributes_empty_string():
    """Test empty GFF attribute string."""
    # Parsing attributes.
    attributes = parse_gff_attributes("")

    # Checking result.
    assert attributes == {}


def test_parse_gff_attributes_ignores_invalid_entries():
    """Test GFF attribute parsing ignores entries without equals signs."""
    # Parsing attributes.
    attributes = parse_gff_attributes("ID=gene_nad1;invalid_entry;Name=nad1")

    # Checking parsed values.
    assert attributes == {
        "ID": "gene_nad1",
        "Name": "nad1",
    }


def test_parse_gff_attributes_preserves_equals_in_values():
    """Test GFF attribute parsing preserves equals signs after first split."""
    # Parsing attributes.
    attributes = parse_gff_attributes("ID=gene1;Note=a=b=c")

    # Checking parsed values.
    assert attributes["ID"] == "gene1"
    assert attributes["Note"] == "a=b=c"


def test_parse_mitos2_gff_missing_file_raises_error(tmp_path):
    """Test parse_mitos2_gff raises for missing file."""
    # Defining missing GFF path.
    gff_path = tmp_path / "missing.gff"

    # Checking error.
    with pytest.raises(FileNotFoundError):
        parse_mitos2_gff(gff_path)


def test_parse_mitos2_gff_directory_raises_error(tmp_path):
    """Test parse_mitos2_gff raises if path is a directory."""
    # Creating directory path.
    gff_path = tmp_path / "result.gff"
    gff_path.mkdir()

    # Checking error.
    with pytest.raises(ValueError):
        parse_mitos2_gff(gff_path)


def test_parse_mitos2_gff_malformed_row_raises_error(tmp_path):
    """Test parse_mitos2_gff raises on malformed rows."""
    # Creating malformed GFF.
    gff_path = tmp_path / "bad.gff"
    write_file(gff_path, "this is not a valid gff row\n")

    # Checking error.
    with pytest.raises(ValueError):
        parse_mitos2_gff(gff_path)


def test_parse_mitos2_gff_parses_features(tmp_path):
    """Test parse_mitos2_gff parses non-comment feature rows."""
    # Creating GFF.
    gff_path = make_mitos2_gff(tmp_path)

    # Parsing GFF.
    features = parse_mitos2_gff(gff_path)

    # Checking feature count.
    assert len(features) == 9


def test_parse_mitos2_gff_skips_comments_and_blank_lines(tmp_path):
    """Test parse_mitos2_gff skips comments and blank lines."""
    # Creating GFF.
    gff_path = tmp_path / "result.gff"
    write_file(
        gff_path,
        "\n##gff-version 3\n\n3185-(circular)\tmitos\tgene\t1\t100\t.\t+\t.\tID=gene_nad1;Name=nad1;gene_id=nad1\n\n",
    )

    # Parsing GFF.
    features = parse_mitos2_gff(gff_path)

    # Checking feature count.
    assert len(features) == 1


def test_parse_mitos2_gff_feature_contains_expected_fields(tmp_path):
    """Test parsed GFF features contain expected dictionary fields."""
    # Creating GFF.
    gff_path = make_mitos2_gff(tmp_path)

    # Parsing GFF.
    features = parse_mitos2_gff(gff_path)
    feature = features[0]

    # Checking fields.
    assert "seqid" in feature
    assert "source" in feature
    assert "type" in feature
    assert "start" in feature
    assert "end" in feature
    assert "score" in feature
    assert "strand" in feature
    assert "phase" in feature
    assert "attributes" in feature
    assert "name" in feature
    assert "gene_id" in feature


def test_parse_mitos2_gff_parses_attributes(tmp_path):
    """Test parsed GFF features include parsed attributes."""
    # Creating GFF.
    gff_path = make_mitos2_gff(tmp_path)

    # Parsing GFF.
    features = parse_mitos2_gff(gff_path)

    # Finding nad1 gene.
    nad1 = [
        feature for feature in features
        if feature["type"] == "gene" and feature["gene_id"] == "nad1"
    ][0]

    # Checking attributes.
    assert nad1["attributes"]["ID"] == "gene_nad1"
    assert nad1["attributes"]["Name"] == "nad1"
    assert nad1["attributes"]["gene_id"] == "nad1"


def test_parse_mitos2_warnings_none_returns_empty_list():
    """Test parse_mitos2_warnings returns empty list when path is None."""
    # Parsing warnings.
    warnings = parse_mitos2_warnings(None)

    # Checking result.
    assert warnings == []


def test_parse_mitos2_warnings_missing_file_returns_empty_list(tmp_path):
    """Test parse_mitos2_warnings returns empty list for missing file."""
    # Parsing warnings.
    warnings = parse_mitos2_warnings(tmp_path / "missing.mitos")

    # Checking result.
    assert warnings == []


def test_parse_mitos2_warnings_extracts_warning_lines(tmp_path):
    """Test parse_mitos2_warnings extracts warning-like lines."""
    # Creating result.mitos.
    mitos_path = tmp_path / "result.mitos"
    write_file(
        mitos_path,
        "normal line\nWARNING: low confidence annotation\nduplicated:2x rrnL\n",
    )

    # Parsing warnings.
    warnings = parse_mitos2_warnings(mitos_path)

    # Checking warnings.
    assert len(warnings) == 2
    assert "WARNING" in warnings[0]
    assert "duplicated" in warnings[1]


def test_parse_annotation_stats_returns_annotation_stats_model(tmp_path):
    """Test parse_annotation_stats returns AnnotationStats."""
    # Creating GFF.
    gff_path = make_mitos2_gff(tmp_path)

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="sample_001",
        gff_path=gff_path,
    )

    # Checking model.
    assert isinstance(stats, AnnotationStats)


def test_parse_annotation_stats_counts_small_fixture(tmp_path):
    """Test parse_annotation_stats counts expected features from small fixture."""
    # Creating GFF.
    gff_path = make_mitos2_gff(tmp_path)

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="sample_001",
        gff_path=gff_path,
    )

    # Checking stats.
    assert stats.sample_id == "sample_001"
    assert stats.cds_count == 1
    assert stats.trna_count == 1
    assert stats.rrna_count == 1
    assert stats.gene_count == 3
    assert stats.feature_count == 9
    assert stats.warnings == []


def test_parse_annotation_stats_counts_full_fixture(tmp_path):
    """Test parse_annotation_stats counts expected canonical mitogenome features."""
    # Creating GFF.
    gff_path = make_full_mitos2_gff(tmp_path)

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="common_carp_001",
        gff_path=gff_path,
    )

    # Checking counts.
    assert stats.sample_id == "common_carp_001"
    assert stats.cds_count == 13
    assert stats.trna_count == 22
    assert stats.rrna_count == 2
    assert stats.gene_count == 37
    assert stats.feature_count == 99
    assert stats.warnings == []


def test_parse_annotation_stats_includes_warnings(tmp_path):
    """Test parse_annotation_stats includes parsed warnings."""
    # Creating files.
    gff_path = make_mitos2_gff(tmp_path)
    mitos_path = tmp_path / "result.mitos"
    write_file(mitos_path, "duplicated:2x rrnL\n")

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="sample_001",
        gff_path=gff_path,
        mitos_path=mitos_path,
    )

    # Checking warnings.
    assert stats.warnings == ["duplicated:2x rrnL"]


def test_parse_annotation_stats_empty_gff_returns_zero_counts(tmp_path):
    """Test parse_annotation_stats returns zero counts for comment-only GFF."""
    # Creating empty/comment-only GFF.
    gff_path = tmp_path / "empty.gff"
    write_file(gff_path, "##gff-version 3\n")

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="sample_001",
        gff_path=gff_path,
    )

    # Checking counts.
    assert stats.cds_count == 0
    assert stats.trna_count == 0
    assert stats.rrna_count == 0
    assert stats.gene_count == 0
    assert stats.feature_count == 0
    assert stats.warnings == []


def test_parse_annotation_stats_does_not_count_unknown_gene_as_cds(tmp_path):
    """Test parse_annotation_stats does not count unknown MITOS gene as CDS."""
    # Creating GFF.
    gff_path = tmp_path / "unknown_gene.gff"
    write_file(
        gff_path,
        "3185-(circular)\tmitos\tgene\t1\t100\t.\t+\t.\tID=gene_unknown;Name=unknown;gene_id=unknown\n",
    )

    # Parsing stats.
    stats = parse_annotation_stats(
        sample_id="sample_001",
        gff_path=gff_path,
    )

    # Checking counts.
    assert stats.cds_count == 0
    assert stats.gene_count == 1
    assert stats.feature_count == 1