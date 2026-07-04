"""test_blast_stats.py

Unit tests for parsing, ranking, selecting, and writing BLAST matches.
"""

# Imports
import csv
from pathlib import Path

import pytest

from mitopipeline.stats.blast_stats import (
    BLAST_COLUMNS,
    parse_blast_tsv,
    rank_blast_matches,
    select_top_blast_matches,
    write_top_blast_matches,
)


def write_file(path: Path, contents: str = "") -> None:
    """Write text to a file, creating parent directories as needed.

    Args:
        path (Path): File path.
        contents (str, optional): File contents. Defaults to an empty string.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def make_match(
    subject_id: str,
    evalue: float,
    bitscore: float,
    query_coverage: float,
    percent_identity: float,
    alignment_length: int,
    query_id: str = "query_001",
    scientific_name: str = "Test species",
    title: str = "Test mitochondrial genome",
) -> dict:
    """Create a representative parsed BLAST match.

    Args:
        subject_id (str): Subject accession.
        evalue (float): BLAST expected value.
        bitscore (float): BLAST bit score.
        query_coverage (float): Query coverage percentage.
        percent_identity (float): Percent identity.
        alignment_length (int): Alignment length.
        query_id (str, optional): Query sequence identifier.
        scientific_name (str, optional): Subject scientific name.
        title (str, optional): Subject sequence title.

    Returns:
        dict: Parsed BLAST match.
    """
    return {
        "qseqid": query_id,
        "sseqid": subject_id,
        "pident": percent_identity,
        "length": alignment_length,
        "mismatch": 2,
        "gapopen": 0,
        "qstart": 1,
        "qend": alignment_length,
        "sstart": 1,
        "send": alignment_length,
        "evalue": evalue,
        "bitscore": bitscore,
        "qcovs": query_coverage,
        "staxids": "12345",
        "sscinames": scientific_name,
        "stitle": title,
    }


def match_to_tsv_row(match: dict) -> str:
    """Convert a BLAST match dictionary to one tab-delimited row.

    Args:
        match (dict): BLAST match.

    Returns:
        str: Tab-delimited BLAST row.
    """
    return "\t".join(str(match[column]) for column in BLAST_COLUMNS)


def test_parse_blast_tsv_parses_valid_rows(tmp_path):
    """Test parse_blast_tsv parses valid BLAST rows."""
    blast_path = tmp_path / "sample.blast.tsv"

    matches = [
        make_match(
            subject_id="NC_000001.1",
            evalue=1e-50,
            bitscore=900.0,
            query_coverage=99.0,
            percent_identity=98.5,
            alignment_length=16000,
        ),
        make_match(
            subject_id="NC_000002.1",
            evalue=1e-40,
            bitscore=850.0,
            query_coverage=97.0,
            percent_identity=97.0,
            alignment_length=15800,
        ),
    ]

    write_file(
        blast_path,
        "\n".join(match_to_tsv_row(match) for match in matches) + "\n",
    )

    parsed = parse_blast_tsv(blast_path)

    assert len(parsed) == 2
    assert parsed[0]["sseqid"] == "NC_000001.1"
    assert parsed[1]["sseqid"] == "NC_000002.1"


def test_parse_blast_tsv_converts_numeric_fields(tmp_path):
    """Test parse_blast_tsv converts numeric columns."""
    blast_path = tmp_path / "sample.blast.tsv"

    match = make_match(
        subject_id="NC_000001.1",
        evalue=1e-50,
        bitscore=900.5,
        query_coverage=99.0,
        percent_identity=98.5,
        alignment_length=16000,
    )

    write_file(blast_path, match_to_tsv_row(match) + "\n")

    parsed = parse_blast_tsv(blast_path)[0]

    for column in ("pident", "evalue", "bitscore", "qcovs"):
        assert isinstance(parsed[column], float)

    for column in (
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
    ):
        assert isinstance(parsed[column], int)


def test_parse_blast_tsv_accepts_empty_file(tmp_path):
    """Test an empty BLAST result returns an empty list."""
    blast_path = tmp_path / "sample.blast.tsv"
    write_file(blast_path)

    assert parse_blast_tsv(blast_path) == []


def test_parse_blast_tsv_ignores_blank_lines(tmp_path):
    """Test parse_blast_tsv ignores blank lines."""
    blast_path = tmp_path / "sample.blast.tsv"

    match = make_match(
        subject_id="NC_000001.1",
        evalue=1e-50,
        bitscore=900.0,
        query_coverage=99.0,
        percent_identity=98.5,
        alignment_length=16000,
    )

    write_file(
        blast_path,
        f"\n{match_to_tsv_row(match)}\n\n",
    )

    assert len(parse_blast_tsv(blast_path)) == 1


def test_parse_blast_tsv_raises_for_missing_file(tmp_path):
    """Test parse_blast_tsv rejects a missing file."""
    with pytest.raises(FileNotFoundError):
        parse_blast_tsv(tmp_path / "missing.blast.tsv")


def test_parse_blast_tsv_raises_for_directory(tmp_path):
    """Test parse_blast_tsv rejects a directory."""
    blast_path = tmp_path / "blast"
    blast_path.mkdir()

    with pytest.raises(ValueError):
        parse_blast_tsv(blast_path)


def test_parse_blast_tsv_raises_for_wrong_column_count(tmp_path):
    """Test parse_blast_tsv rejects rows with an incorrect schema."""
    blast_path = tmp_path / "sample.blast.tsv"
    write_file(blast_path, "query_001\tNC_000001.1\t99.0\n")

    with pytest.raises(ValueError, match="expected"):
        parse_blast_tsv(blast_path)


def test_parse_blast_tsv_raises_for_invalid_numeric_data(tmp_path):
    """Test parse_blast_tsv rejects invalid numeric values."""
    blast_path = tmp_path / "sample.blast.tsv"

    match = make_match(
        subject_id="NC_000001.1",
        evalue=1e-50,
        bitscore=900.0,
        query_coverage=99.0,
        percent_identity=98.5,
        alignment_length=16000,
    )
    match["bitscore"] = "invalid"

    write_file(blast_path, match_to_tsv_row(match) + "\n")

    with pytest.raises(
        ValueError,
        match=r"Error parsing BLAST row 1",
    ):
        parse_blast_tsv(blast_path)


def test_rank_blast_matches_uses_expected_ranking_order():
    """Test ranking uses e-value, bit score, coverage, identity, and length."""
    matches = [
        make_match(
            subject_id="NC_EVALUE.1",
            evalue=1e-100,
            bitscore=500.0,
            query_coverage=80.0,
            percent_identity=80.0,
            alignment_length=12000,
        ),
        make_match(
            subject_id="NC_BITSCORE.1",
            evalue=1e-50,
            bitscore=950.0,
            query_coverage=90.0,
            percent_identity=90.0,
            alignment_length=14000,
        ),
        make_match(
            subject_id="NC_COVERAGE.1",
            evalue=1e-50,
            bitscore=900.0,
            query_coverage=99.0,
            percent_identity=90.0,
            alignment_length=14000,
        ),
        make_match(
            subject_id="NC_IDENTITY.1",
            evalue=1e-50,
            bitscore=900.0,
            query_coverage=95.0,
            percent_identity=99.0,
            alignment_length=14000,
        ),
        make_match(
            subject_id="NC_LENGTH.1",
            evalue=1e-50,
            bitscore=900.0,
            query_coverage=95.0,
            percent_identity=95.0,
            alignment_length=16000,
        ),
    ]

    ranked = rank_blast_matches(matches)

    assert [match["sseqid"] for match in ranked] == [
        "NC_EVALUE.1",
        "NC_BITSCORE.1",
        "NC_COVERAGE.1",
        "NC_IDENTITY.1",
        "NC_LENGTH.1",
    ]


def test_rank_blast_matches_collapses_duplicate_accessions():
    """Test duplicate accessions retain their strongest alignment."""
    matches = [
        make_match(
            subject_id="NC_000001.1",
            evalue=1e-20,
            bitscore=500.0,
            query_coverage=90.0,
            percent_identity=95.0,
            alignment_length=15000,
        ),
        make_match(
            subject_id="NC_000001.1",
            evalue=1e-50,
            bitscore=800.0,
            query_coverage=99.0,
            percent_identity=99.0,
            alignment_length=16000,
        ),
    ]

    ranked = rank_blast_matches(matches)

    assert len(ranked) == 1
    assert ranked[0]["evalue"] == 1e-50
    assert ranked[0]["bitscore"] == 800.0


def test_rank_blast_matches_is_deterministic_for_complete_ties():
    """Test accession ID resolves otherwise identical ties."""
    matches = [
        make_match(
            subject_id="NC_000002.1",
            evalue=0.0,
            bitscore=900.0,
            query_coverage=99.0,
            percent_identity=99.0,
            alignment_length=16000,
        ),
        make_match(
            subject_id="NC_000001.1",
            evalue=0.0,
            bitscore=900.0,
            query_coverage=99.0,
            percent_identity=99.0,
            alignment_length=16000,
        ),
    ]

    ranked = rank_blast_matches(matches)

    assert [match["sseqid"] for match in ranked] == [
        "NC_000001.1",
        "NC_000002.1",
    ]


def test_select_top_blast_matches_returns_six_ranked_unique_hits():
    """Test top-hit selection returns six ranked unique accessions."""
    matches = [
        make_match(
            subject_id=f"NC_{index:06d}.1",
            evalue=10 ** -(100 - index),
            bitscore=1000.0 - index,
            query_coverage=99.0,
            percent_identity=99.0,
            alignment_length=16000 - index,
        )
        for index in range(10)
    ]

    selected = select_top_blast_matches(
        matches,
        maximum_matches=6,
    )

    assert len(selected) == 6
    assert [match["rank"] for match in selected] == [1, 2, 3, 4, 5, 6]
    assert len({match["sseqid"] for match in selected}) == 6


def test_select_top_blast_matches_returns_all_available_hits():
    """Test selection returns fewer than six when fewer are available."""
    matches = [
        make_match(
            subject_id="NC_000001.1",
            evalue=1e-50,
            bitscore=900.0,
            query_coverage=99.0,
            percent_identity=99.0,
            alignment_length=16000,
        ),
        make_match(
            subject_id="NC_000002.1",
            evalue=1e-40,
            bitscore=850.0,
            query_coverage=98.0,
            percent_identity=98.0,
            alignment_length=15900,
        ),
    ]

    selected = select_top_blast_matches(
        matches,
        maximum_matches=6,
    )

    assert len(selected) == 2
    assert [match["rank"] for match in selected] == [1, 2]


def test_select_top_blast_matches_accepts_no_hits():
    """Test selection returns an empty list when BLAST has no hits."""
    assert select_top_blast_matches([], maximum_matches=6) == []


@pytest.mark.parametrize("maximum_matches", [0, -1])
def test_select_top_blast_matches_rejects_invalid_maximum(
    maximum_matches,
):
    """Test selection rejects non-positive maximum match counts."""
    with pytest.raises(ValueError):
        select_top_blast_matches(
            [],
            maximum_matches=maximum_matches,
        )


def test_write_top_blast_matches_writes_expected_tsv(tmp_path):
    """Test selected BLAST matches are written with metadata."""
    output_path = tmp_path / "sample.top_hits.tsv"

    selected = [
        {
            **make_match(
                subject_id="NC_000001.1",
                evalue=1e-50,
                bitscore=900.0,
                query_coverage=99.0,
                percent_identity=99.0,
                alignment_length=16000,
            ),
            "rank": 1,
        }
    ]

    write_top_blast_matches(
        matches=selected,
        output_path=output_path,
        sample_id="sample_001",
    )

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert len(rows) == 1
    assert rows[0]["sample_id"] == "sample_001"
    assert rows[0]["rank"] == "1"
    assert rows[0]["sseqid"] == "NC_000001.1"
    assert rows[0]["sscinames"] == "Test species"


def test_write_top_blast_matches_writes_header_for_no_hits(tmp_path):
    """Test no-hit output still contains a valid TSV header."""
    output_path = tmp_path / "sample.top_hits.tsv"

    write_top_blast_matches(
        matches=[],
        output_path=output_path,
        sample_id="sample_001",
    )

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    assert reader.fieldnames == [
        "sample_id",
        "rank",
        *BLAST_COLUMNS,
    ]
    assert rows == []