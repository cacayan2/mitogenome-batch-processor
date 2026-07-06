"""test_alignment_dataset.py

Unit tests for phylogenetic alignment-dataset generation.
"""

# Imports
from pathlib import Path

import pytest
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from mitopipeline.stats.alignment_dataset import (
    build_assembled_sequence_name,
    build_reference_sequence_name,
    generate_alignment_dataset,
    normalize_blast_accession,
    order_and_standardize_reference_sequences,
    parse_top_blast_hits,
    read_assembled_genome,
    standardize_sequence_name,
    validate_alignment_dataset,
)


def test_normalize_blast_accession_plain():
    """Confirm plain accessions remain unchanged."""
    accession = normalize_blast_accession(
        "NC_012345.1"
    )

    assert accession == "NC_012345.1"


def test_normalize_blast_accession_refseq():
    """Confirm RefSeq identifiers are normalized."""
    accession = normalize_blast_accession(
        "ref|NC_012345.1|"
    )

    assert accession == "NC_012345.1"


def test_normalize_blast_accession_genbank():
    """Confirm GenBank identifiers are normalized."""
    accession = normalize_blast_accession(
        "gb|MW123456.1|"
    )

    assert accession == "MW123456.1"


def test_normalize_blast_accession_empty_raises():
    """Confirm empty subject identifiers raise an error."""
    with pytest.raises(
            ValueError,
            match="cannot be empty",
    ):
        normalize_blast_accession("")


def test_standardize_sequence_name():
    """Confirm sequence-name text is standardized."""
    name = standardize_sequence_name(
        "Etheostoma blennioides (sample)"
    )

    assert name == (
        "Etheostoma_blennioides_sample"
    )


def test_build_assembled_sequence_name():
    """Confirm the assembled-genome name is deterministic."""
    name = build_assembled_sequence_name(
        "sample 001"
    )

    assert name == "sample_001|assembled"


def test_build_reference_sequence_name():
    """Confirm reference names include rank and accession."""
    name = build_reference_sequence_name(
        rank=2,
        accession="NC_012345.1",
        scientific_name="Etheostoma blennioides",
    )

    assert name == (
        "reference_02"
        "|NC_012345.1"
        "|Etheostoma_blennioides"
    )


def test_parse_top_blast_hits_preserves_rank(
        tmp_path: Path,
):
    """Confirm selected BLAST hits are ordered by rank."""
    top_hits_path = (
        tmp_path
        / "sample.top_hits.tsv"
    )

    top_hits_path.write_text(
        (
            "sample_id\trank\tsseqid\tsscinames\n"
            "sample_001\t2\tNC_000002.1\tSpecies two\n"
            "sample_001\t1\tNC_000001.1\tSpecies one\n"
        ),
        encoding="utf-8",
    )

    matches = parse_top_blast_hits(
        top_hits_path
    )

    assert len(matches) == 2
    assert matches[0]["rank"] == 1
    assert matches[1]["rank"] == 2


def test_parse_top_blast_hits_missing_file_raises(
        tmp_path: Path,
):
    """Confirm a missing selected-hit file raises an error."""
    top_hits_path = (
        tmp_path
        / "missing.tsv"
    )

    with pytest.raises(
            FileNotFoundError,
    ):
        parse_top_blast_hits(
            top_hits_path
        )


def test_read_assembled_genome(
        tmp_path: Path,
):
    """Confirm one assembled genome is read and renamed."""
    assembly_path = (
        tmp_path
        / "sample.fasta"
    )

    assembly_path.write_text(
        ">contig_1\nATGCGT\n",
        encoding="utf-8",
    )

    record = read_assembled_genome(
        assembly_fasta=assembly_path,
        sample_id="sample_001",
    )

    assert record.id == "sample_001|assembled"
    assert str(record.seq) == "ATGCGT"


def test_read_assembled_genome_multiple_records_raises(
        tmp_path: Path,
):
    """Confirm multiple assembly records raise an error."""
    assembly_path = (
        tmp_path
        / "sample.fasta"
    )

    assembly_path.write_text(
        (
            ">contig_1\nATGC\n"
            ">contig_2\nGTAC\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="exactly one",
    ):
        read_assembled_genome(
            assembly_fasta=assembly_path,
            sample_id="sample_001",
        )


def test_order_and_standardize_reference_sequences():
    """Confirm retrieved references follow BLAST rank."""
    matches = [
        {
            "rank": 1,
            "sseqid": "NC_000001.1",
            "sscinames": "Species one",
        },
        {
            "rank": 2,
            "sseqid": "NC_000002.1",
            "sscinames": "Species two",
        },
    ]

    retrieved_records = [
        SeqRecord(
            Seq("CCCC"),
            id="NC_000002.1",
        ),
        SeqRecord(
            Seq("AAAA"),
            id="NC_000001.1",
        ),
    ]

    records = (
        order_and_standardize_reference_sequences(
            matches=matches,
            retrieved_records=retrieved_records,
        )
    )

    assert records[0].id == (
        "reference_01"
        "|NC_000001.1"
        "|Species_one"
    )

    assert records[1].id == (
        "reference_02"
        "|NC_000002.1"
        "|Species_two"
    )


def test_order_reference_sequences_missing_accession_raises():
    """Confirm missing retrieved accessions raise an error."""
    matches = [
        {
            "rank": 1,
            "sseqid": "NC_000001.1",
            "sscinames": "Species one",
        },
    ]

    retrieved_records = [
        SeqRecord(
            Seq("AAAA"),
            id="NC_999999.1",
        ),
    ]

    with pytest.raises(
            ValueError,
            match="did not return",
    ):
        order_and_standardize_reference_sequences(
            matches=matches,
            retrieved_records=retrieved_records,
        )


def test_validate_alignment_dataset_duplicate_ids_raises():
    """Confirm duplicate output identifiers raise an error."""
    records = [
        SeqRecord(
            Seq("AAAA"),
            id="sample_001|assembled",
        ),
        SeqRecord(
            Seq("CCCC"),
            id="reference_01",
        ),
        SeqRecord(
            Seq("GGGG"),
            id="reference_01",
        ),
    ]

    with pytest.raises(
            ValueError,
            match="Duplicate",
    ):
        validate_alignment_dataset(
            records=records,
            expected_reference_count=2,
        )


def test_generate_alignment_dataset(
        tmp_path: Path,
):
    """Confirm a complete combined FASTA is generated."""
    assembly_path = (
        tmp_path
        / "sample.fasta"
    )

    top_hits_path = (
        tmp_path
        / "sample.top_hits.tsv"
    )

    output_path = (
        tmp_path
        / "sample.phylogeny.fasta"
    )

    assembly_path.write_text(
        ">contig_1\nATGCGT\n",
        encoding="utf-8",
    )

    top_hits_path.write_text(
        (
            "sample_id\trank\tsseqid\tsscinames\n"
            "sample_001\t1\tNC_000001.1\tSpecies one\n"
            "sample_001\t2\tNC_000002.1\tSpecies two\n"
        ),
        encoding="utf-8",
    )

    def fake_retrieve_function(
            accessions,
            entrez_email,
            entrez_api_key=None,
            logger=None,
    ):
        assert accessions == [
            "NC_000001.1",
            "NC_000002.1",
        ]

        assert entrez_email == (
            "test@example.com"
        )

        return [
            SeqRecord(
                Seq("AAAA"),
                id="NC_000001.1",
            ),
            SeqRecord(
                Seq("CCCC"),
                id="NC_000002.1",
            ),
        ]

    generate_alignment_dataset(
        sample_id="sample_001",
        assembly_fasta=assembly_path,
        top_hits_tsv=top_hits_path,
        output_fasta=output_path,
        entrez_email="test@example.com",
        retrieve_function=fake_retrieve_function,
    )

    records = list(
        SeqIO.parse(
            output_path,
            "fasta",
        )
    )

    assert len(records) == 3

    assert records[0].id == (
        "sample_001|assembled"
    )

    assert records[1].id == (
        "reference_01"
        "|NC_000001.1"
        "|Species_one"
    )

    assert records[2].id == (
        "reference_02"
        "|NC_000002.1"
        "|Species_two"
    )

    assert str(records[0].seq) == "ATGCGT"
    assert str(records[1].seq) == "AAAA"
    assert str(records[2].seq) == "CCCC"