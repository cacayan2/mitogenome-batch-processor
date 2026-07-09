"""test_archival_metadata.py

Unit tests for NCBI archival metadata schema validation.
"""

# Imports
from pathlib import Path

import pandas as pd

from mitopipeline.config.archival_metadata import (
    ARCHIVAL_COLUMNS,
    validate_archival_metadata_file,
    validate_archival_metadata_table,
    write_example_archival_metadata,
)


def make_valid_table() -> pd.DataFrame:
    """Create a valid archival metadata table."""
    row = {
        column: "missing"
        for column in ARCHIVAL_COLUMNS
    }

    row.update(
        {
            "sample_id": "sample_001",
            "organism": "Negaprion brevirostris",
            "sample_title": "Lemon shark mitochondrial genome sample",
            "bioproject_title": "Mitochondrial genome reference panel",
            "bioproject_description": (
                "Mitochondrial genome assembly and validation."
            ),
            "biosample_package": "Model organism or animal",
            "isolate": "sample_001",
            "collection_date": "not collected",
            "geo_loc_name": "not collected",
            "library_strategy": "WGS",
            "library_source": "GENOMIC",
            "library_selection": "RANDOM",
            "library_layout": "paired",
            "platform": "ILLUMINA",
            "instrument_model": "missing",
            "read_1_filename": "sample_001_R1.fastq.gz",
            "read_2_filename": "sample_001_R2.fastq.gz",
            "assembly_fasta_filename": "sample_001.fasta",
            "assembly_method": "GetOrganelle; version missing",
            "annotation_method": "MITOS2; version missing",
            "molecule_type": "genomic DNA",
            "genome_location": "mitochondrion",
            "environmental_sample": "false",
            "circular": "missing",
        }
    )

    return pd.DataFrame(
        [
            row
        ],
        columns=ARCHIVAL_COLUMNS,
    )


def test_validate_archival_metadata_table_valid():
    """Confirm a valid table passes validation."""
    result = validate_archival_metadata_table(
        make_valid_table()
    )

    assert result.valid is True
    assert result.errors == []
    assert result.row_count == 1


def test_validate_archival_metadata_table_missing_required_value():
    """Confirm empty required values fail validation."""
    table = make_valid_table()

    table.loc[
        0,
        "organism",
    ] = ""

    result = validate_archival_metadata_table(
        table
    )

    assert result.valid is False
    assert any(
        "organism is empty"
        in error
        for error in result.errors
    )


def test_validate_archival_metadata_table_duplicate_sample_id():
    """Confirm duplicate sample IDs fail validation."""
    table = pd.concat(
        [
            make_valid_table(),
            make_valid_table(),
        ],
        ignore_index=True,
    )

    result = validate_archival_metadata_table(
        table
    )

    assert result.valid is False
    assert any(
        "Duplicate sample_id"
        in error
        for error in result.errors
    )


def test_validate_archival_metadata_table_paired_requires_r2():
    """Confirm paired libraries require read_2_filename."""
    table = make_valid_table()

    table.loc[
        0,
        "read_2_filename",
    ] = ""

    result = validate_archival_metadata_table(
        table
    )

    assert result.valid is False
    assert any(
        "read_2_filename is required"
        in error
        for error in result.errors
    )


def test_validate_archival_metadata_table_invalid_boolean():
    """Confirm boolean-like fields are controlled."""
    table = make_valid_table()

    table.loc[
        0,
        "environmental_sample",
    ] = "maybe"

    result = validate_archival_metadata_table(
        table
    )

    assert result.valid is False
    assert any(
        "environmental_sample"
        in error
        for error in result.errors
    )


def test_validate_archival_metadata_file(
        tmp_path: Path,
):
    """Confirm TSV validation works from disk."""
    metadata_path = (
        tmp_path
        / "archival_metadata.tsv"
    )

    make_valid_table().to_csv(
        metadata_path,
        sep="\t",
        index=False,
    )

    result = validate_archival_metadata_file(
        metadata_path
    )

    assert result.valid is True


def test_write_example_archival_metadata(
        tmp_path: Path,
):
    """Confirm example archival metadata can be written."""
    output_path = (
        tmp_path
        / "archival_metadata.tsv"
    )

    result = write_example_archival_metadata(
        output_path
    )

    assert result == output_path.resolve()
    assert output_path.exists()

    validation = validate_archival_metadata_file(
        output_path
    )

    assert validation.valid is True
