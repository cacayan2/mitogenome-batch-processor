"""test_assembly_stats.py

Unit tests for assembly statistics parsing.
"""

# Imports
from pathlib import Path
import pytest

from mitopipeline.stats.assembly_stats import (
    parse_fasta_sequences,
    calculate_gc_content_percent,
    infer_circularization_status,
    parse_assembly_stats,
)

def create_fasta_file(fasta_path: Path, fasta_text: str) -> None:
    """Create a minimal FASTA fixture."""

    # Creating parent directory.
    fasta_path.parent.mkdir(parents=True, exist_ok=True)

    # Writing FASTA contents.
    fasta_path.write_text(fasta_text, encoding="utf-8")


def test_parse_fasta_sequences_valid_fasta(tmp_path):
    """Unit test confirming a valid FASTA file parses correctly."""

    # Defining test paths.
    fasta_path = tmp_path / "assembly.fasta"

    # Defining FASTA text.
    fasta_text = (
        ">contig1\n"
        "AACCGG\n"
        ">contig2\n"
        "TTAA\n"
    )

    # Creating FASTA fixture.
    create_fasta_file(fasta_path, fasta_text)

    # Parsing FASTA sequences.
    sequences = parse_fasta_sequences(
        fasta_path=fasta_path,
        logger=None,
    )

    # Assert statements.
    assert sequences == {
        "contig1": "AACCGG",
        "contig2": "TTAA",
    }


def test_parse_fasta_sequences_missing_header_raises_error(tmp_path):
    """Unit test confirming FASTA sequence before header raises ValueError."""

    # Defining test paths.
    fasta_path = tmp_path / "missing_header.fasta"

    # Creating malformed FASTA fixture.
    create_fasta_file(fasta_path, "AACCGG\n")

    # Assert statements.
    with pytest.raises(ValueError):
        parse_fasta_sequences(
            fasta_path=fasta_path,
            logger=None,
        )


def test_calculate_gc_content_percent():
    """Unit test confirming GC content is calculated correctly."""

    # Assert statements.
    assert calculate_gc_content_percent(
        sequence="AAGGCC",
        logger=None,
    ) == 66.67


def test_calculate_gc_content_percent_empty_sequence_returns_zero():
    """Unit test confirming empty sequence returns zero GC content."""

    # Assert statements.
    assert calculate_gc_content_percent(
        sequence="",
        logger=None,
    ) == 0.0


def test_calculate_gc_content_percent_ignores_non_acgt_bases():
    """Unit test confirming ambiguous bases are ignored in GC calculation."""

    # Assert statements.
    assert calculate_gc_content_percent(
        sequence="AAGGCCNNNN",
        logger=None,
    ) == 66.67


def test_infer_circularization_status_complete():
    """Unit test confirming complete/circular filename returns complete."""

    # Defining test path.
    fasta_path = Path("animal_mt.K115.complete.graph1.1.path_sequence.fasta")

    # Assert statements.
    assert infer_circularization_status(
        fasta_path=fasta_path,
        logger=None,
    ) == "complete"


def test_infer_circularization_status_incomplete():
    """Unit test confirming scaffold/linear filename returns incomplete."""

    # Defining test path.
    fasta_path = Path("animal_mt.K115.scaffold.graph1.path_sequence.fasta")

    # Assert statements.
    assert infer_circularization_status(
        fasta_path=fasta_path,
        logger=None,
    ) == "incomplete"


def test_infer_circularization_status_unknown():
    """Unit test confirming uninformative filename returns None."""

    # Defining test path.
    fasta_path = Path("common_carp_001.fasta")

    # Assert statements.
    assert infer_circularization_status(
        fasta_path=fasta_path,
        logger=None,
    ) is None


def test_parse_assembly_stats_valid_fasta(tmp_path):
    """Unit test confirming assembly statistics parse from a valid FASTA."""

    # Defining test paths.
    fasta_path = tmp_path / "animal_mt.K115.complete.graph1.1.path_sequence.fasta"

    # Defining FASTA text.
    fasta_text = (
        ">contig1\n"
        "AACCGG\n"
        ">contig2\n"
        "TTAA\n"
    )

    # Creating FASTA fixture.
    create_fasta_file(fasta_path, fasta_text)

    # Parsing assembly statistics.
    stats = parse_assembly_stats(
        sample_id="common_carp_001",
        fasta_path=fasta_path,
        runtime_seconds=123.4,
        logger=None,
    )

    # Assert statements.
    assert stats.sample_id == "common_carp_001"
    assert stats.fasta_path == fasta_path
    assert stats.contig_count == 2
    assert stats.total_length_bp == 10
    assert stats.gc_content_percent == 40.0
    assert stats.circularization_status == "complete"
    assert stats.runtime_seconds == 123.4


def test_parse_assembly_stats_missing_file_raises_error(tmp_path):
    """Unit test confirming missing assembly FASTA raises FileNotFoundError."""

    # Defining missing path.
    fasta_path = tmp_path / "missing.fasta"

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        parse_assembly_stats(
            sample_id="missing_sample",
            fasta_path=fasta_path,
            runtime_seconds=None,
            logger=None,
        )


def test_parse_assembly_stats_empty_fasta_raises_error(tmp_path):
    """Unit test confirming empty assembly FASTA raises ValueError."""

    # Defining test paths.
    fasta_path = tmp_path / "empty.fasta"

    # Creating empty FASTA fixture.
    create_fasta_file(fasta_path, "")

    # Assert statements.
    with pytest.raises(ValueError):
        parse_assembly_stats(
            sample_id="empty_sample",
            fasta_path=fasta_path,
            runtime_seconds=None,
            logger=None,
        )