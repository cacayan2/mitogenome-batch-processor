"""test_blast_config.py

Unit tests for BLAST switchboard configuration.
"""

# Imports
from pathlib import Path

import pytest

from mitopipeline.config.blast_config import BlastConfig


def make_config(**overrides) -> dict:
    """Create complete BLAST switchboard configuration."""
    config = {
        "mode": "local",
        "database_source": "ncbi",
        "database_name": "refseq_genomic",
        "database_dir": "resources/blast",
        "reference_fasta": (
            "resources/blast/reference_mitogenomes.fasta"
        ),
        "database_title": (
            "MitoPipeline mitochondrial reference database"
        ),
        "initialize_database": True,
        "overwrite_database": False,
        "parse_seqids": True,
        "threads": 4,
        "task": "blastn",
        "evalue": 1e-5,
        "max_target_seqs": 50,
        "max_hsps": 1,
        "maximum_matches": 6,
        "perc_identity": None,
        "query_coverage": None,
        "word_size": None,
        "output_format": "6 qseqid sseqid",
    }

    config.update(overrides)

    return config


def test_local_ncbi_configuration_derives_database_prefix():
    """Test local NCBI mode derives its local database path."""
    settings = BlastConfig.from_mapping(
        make_config()
    )

    assert settings.mode == "local"
    assert settings.database_source == "ncbi"
    assert settings.database_prefix == Path(
        "resources/blast/refseq_genomic"
    )
    assert settings.database_argument == str(
        Path(
            "resources/blast/refseq_genomic"
        ).resolve()
    )
    assert settings.requires_database_setup is True
    assert settings.uses_ncbi_download is True
    assert settings.uses_reference_fasta is False


def test_local_fasta_configuration_uses_same_fields():
    """Test switching source requires changing values only."""
    settings = BlastConfig.from_mapping(
        make_config(
            database_source="fasta",
            database_name="fish_mitogenomes",
        )
    )

    assert settings.database_prefix == Path(
        "resources/blast/fish_mitogenomes"
    )
    assert settings.uses_reference_fasta is True
    assert settings.uses_ncbi_download is False
    assert settings.requires_database_setup is True


def test_remote_configuration_uses_database_name_directly():
    """Test remote mode uses database_name as the NCBI database."""
    settings = BlastConfig.from_mapping(
        make_config(
            mode="remote",
        )
    )

    assert settings.database_argument == "refseq_genomic"
    assert settings.requires_database_setup is False
    assert settings.uses_ncbi_download is False
    assert settings.uses_reference_fasta is False


def test_remote_mode_ignores_database_source():
    """Test database_source does not affect remote execution."""
    ncbi_settings = BlastConfig.from_mapping(
        make_config(
            mode="remote",
            database_source="ncbi",
        )
    )
    fasta_settings = BlastConfig.from_mapping(
        make_config(
            mode="remote",
            database_source="fasta",
        )
    )

    assert (
        ncbi_settings.database_argument
        == fasta_settings.database_argument
        == "refseq_genomic"
    )
    assert ncbi_settings.requires_database_setup is False
    assert fasta_settings.requires_database_setup is False


def test_initialize_database_false_disables_setup_dependency():
    """Test local users may supply an already-installed database."""
    settings = BlastConfig.from_mapping(
        make_config(
            initialize_database=False,
        )
    )

    assert settings.mode == "local"
    assert settings.requires_database_setup is False


@pytest.mark.parametrize(
    "mode",
    [
        "",
        "web",
        "invalid",
    ],
)
def test_invalid_mode_is_rejected(mode):
    """Test unsupported modes are rejected."""
    with pytest.raises(
        ValueError,
        match="Unsupported BLAST mode",
    ):
        BlastConfig.from_mapping(
            make_config(mode=mode)
        )


@pytest.mark.parametrize(
    "source",
    [
        "",
        "zenodo",
        "invalid",
    ],
)
def test_invalid_database_source_is_rejected(source):
    """Test unsupported database sources are rejected."""
    with pytest.raises(
        ValueError,
        match="Unsupported BLAST database source",
    ):
        BlastConfig.from_mapping(
            make_config(database_source=source)
        )


def test_empty_database_name_is_rejected():
    """Test database_name must not be empty."""
    with pytest.raises(
        ValueError,
        match="database_name must not be empty",
    ):
        BlastConfig.from_mapping(
            make_config(database_name="")
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("threads", 0),
        ("evalue", 0),
        ("max_target_seqs", 0),
        ("max_hsps", 0),
        ("maximum_matches", 0),
        ("word_size", 0),
    ],
)
def test_nonpositive_numeric_values_are_rejected(
    field,
    value,
):
    """Test positive numeric options are enforced."""
    with pytest.raises(ValueError):
        BlastConfig.from_mapping(
            make_config(**{field: value})
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("perc_identity", -1),
        ("perc_identity", 101),
        ("query_coverage", -1),
        ("query_coverage", 101),
    ],
)
def test_invalid_percentages_are_rejected(
    field,
    value,
):
    """Test percentage options remain within 0-100."""
    with pytest.raises(ValueError):
        BlastConfig.from_mapping(
            make_config(**{field: value})
        )