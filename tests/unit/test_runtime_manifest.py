"""test_runtime_manifest.py

Unit tests for runtime-manifest normalization and FASTQ discovery.
"""

# Imports
from pathlib import Path

import pandas as pd
import pytest

from mitopipeline.config.runtime_manifest import (
    construct_manifest_from_directory,
    convert_row_per_read_manifest,
    convert_row_per_sample_manifest,
    load_source_manifest,
    normalize_source_columns,
    parse_fastq_filename,
    prepare_runtime_manifest,
    read_source_manifest,
    resolve_input_filename,
)


def create_fastq(
        path: Path,
) -> Path:
    """Create a minimal FASTQ fixture."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        "@read1\nACGT\n+\nIIII\n",
        encoding="utf-8",
    )

    return path


@pytest.mark.parametrize(
    (
        "filename",
        "expected",
    ),
    [
        (
            "sample_001_R1.fastq.gz",
            (
                "sample_001",
                1,
            ),
        ),
        (
            "sample_001_R2.fastq.gz",
            (
                "sample_001",
                2,
            ),
        ),
        (
            "sample_001_R1_001.fastq.gz",
            (
                "sample_001",
                1,
            ),
        ),
        (
            "sample_001_R2_001.fastq.gz",
            (
                "sample_001",
                2,
            ),
        ),
        (
            "sample_001_R1_001",
            (
                "sample_001",
                1,
            ),
        ),
        (
            "sample_001_R2_001",
            (
                "sample_001",
                2,
            ),
        ),
        (
            "sample_001_1.fq.gz",
            (
                "sample_001",
                1,
            ),
        ),
        (
            "sample_001_2.fq.gz",
            (
                "sample_001",
                2,
            ),
        ),
    ],
)
def test_parse_fastq_filename(
        filename: str,
        expected: tuple[str, int],
):
    """Confirm supported paired-end names are parsed."""
    assert parse_fastq_filename(
        filename
    ) == expected


def test_parse_fastq_filename_unsupported():
    """Confirm unsupported filenames return None."""
    assert parse_fastq_filename(
        "sample.fastq.gz"
    ) is None


def test_normalize_source_columns():
    """Confirm workbook headings become canonical fields."""
    table = pd.DataFrame(
        columns=[
            "run",
            "sample_number",
            "genus",
            "species",
            "subspecies",
            "museum",
            "mus_ID",
            "tube_ID",
            "conc_ng_ul",
            "Fastq_name_R1_R2",
            "Dups",
            "GC",
            "Median len",
            "Seqs",
        ]
    )

    result = normalize_source_columns(
        table
    )

    assert "mus_id" in result.columns
    assert "tube_id" in result.columns
    assert "fastq_filename" in result.columns
    assert "sample_number" not in result.columns
    assert "dups" not in result.columns
    assert "gc" not in result.columns
    assert "median_len" not in result.columns
    assert "seqs" not in result.columns


def test_resolve_input_filename_adds_fastq_extension(
        tmp_path: Path,
):
    """Confirm extensionless manifest names resolve."""
    input_directory = (
        tmp_path
        / "reads"
    )

    expected_path = create_fastq(
        input_directory
        / "sample_001_R1_001.fastq.gz"
    )

    result = resolve_input_filename(
        filename="sample_001_R1_001",
        input_directory=input_directory,
    )

    assert result == expected_path.resolve()


def test_resolve_input_filename_rejects_relative_path(
        tmp_path: Path,
):
    """Confirm source manifests use filenames rather than paths."""
    with pytest.raises(
            ValueError,
            match="filenames only",
    ):
        resolve_input_filename(
            filename="../reads/sample_R1.fastq.gz",
            input_directory=tmp_path,
        )


def test_convert_row_per_sample_manifest(
        tmp_path: Path,
):
    """Confirm conventional manifests resolve filenames."""
    input_directory = (
        tmp_path
        / "reads"
    )

    r1_path = create_fastq(
        input_directory
        / "sample_001_R1.fastq.gz"
    )

    r2_path = create_fastq(
        input_directory
        / "sample_001_R2.fastq.gz"
    )

    table = pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "r1": r1_path.name,
                "r2": r2_path.name,
                "genus": "Semotilus",
                "species": "atromaculatus",
            }
        ]
    )

    result = convert_row_per_sample_manifest(
        table=table,
        input_directory=input_directory,
    )

    assert len(result) == 1
    assert result.loc[
        0,
        "sample_id",
    ] == "sample_001"
    assert result.loc[
        0,
        "r1",
    ] == str(r1_path.resolve())
    assert result.loc[
        0,
        "r2",
    ] == str(r2_path.resolve())


def test_convert_row_per_read_manifest(
        tmp_path: Path,
):
    """Confirm Dr. Stuart's row-per-read format is paired."""
    input_directory = (
        tmp_path
        / "reads"
    )

    r1_name = (
        "1_FMNH_118394_TATCTTCAGC-"
        "CGAATATTGG_L001_R1_001.fastq.gz"
    )

    r2_name = (
        "1_FMNH_118394_TATCTTCAGC-"
        "CGAATATTGG_L001_R2_001.fastq.gz"
    )

    create_fastq(
        input_directory
        / r1_name
    )

    create_fastq(
        input_directory
        / r2_name
    )

    table = pd.DataFrame(
        [
            {
                "run": "run_May2026",
                "genus": "Semotilus",
                "species": "atromaculatus",
                "subspecies": "NA",
                "museum": "FMNH",
                "mus_id": "FMNH 118394",
                "tube_id": "FMNH 118394",
                "conc_ng_ul": "6.35",
                "fastq_filename": r1_name.removesuffix(
                    ".fastq.gz"
                ),
            },
            {
                "run": "run_May2026",
                "genus": "Semotilus",
                "species": "atromaculatus",
                "subspecies": "NA",
                "museum": "FMNH",
                "mus_id": "FMNH 118394",
                "tube_id": "FMNH 118394",
                "conc_ng_ul": "6.35",
                "fastq_filename": r2_name.removesuffix(
                    ".fastq.gz"
                ),
            },
        ]
    )

    result = convert_row_per_read_manifest(
        table=table,
        input_directory=input_directory,
    )

    assert len(result) == 1

    assert result.loc[
        0,
        "sample_id",
    ] == (
        "1_FMNH_118394_TATCTTCAGC-"
        "CGAATATTGG_L001"
    )

    assert result.loc[
        0,
        "genus",
    ] == "Semotilus"

    assert result.loc[
        0,
        "species",
    ] == "atromaculatus"

    assert result.loc[
        0,
        "mus_id",
    ] == "FMNH 118394"


def test_convert_row_per_read_manifest_conflicting_metadata(
        tmp_path: Path,
):
    """Confirm mismatched pair metadata raises an error."""
    input_directory = (
        tmp_path
        / "reads"
    )

    create_fastq(
        input_directory
        / "sample_R1_001.fastq.gz"
    )

    create_fastq(
        input_directory
        / "sample_R2_001.fastq.gz"
    )

    table = pd.DataFrame(
        [
            {
                "fastq_filename": "sample_R1_001",
                "genus": "Semotilus",
            },
            {
                "fastq_filename": "sample_R2_001",
                "genus": "Noturus",
            },
        ]
    )

    with pytest.raises(
            ValueError,
            match="Conflicting genus",
    ):
        convert_row_per_read_manifest(
            table=table,
            input_directory=input_directory,
        )


def test_construct_manifest_from_directory(
        tmp_path: Path,
):
    """Confirm paired FASTQs generate a minimal manifest."""
    r1_path = create_fastq(
        tmp_path
        / "nested"
        / "sample_001_R1.fastq.gz"
    )

    r2_path = create_fastq(
        tmp_path
        / "nested"
        / "sample_001_R2.fastq.gz"
    )

    table = construct_manifest_from_directory(
        tmp_path
    )

    assert list(
        table.columns
    ) == [
        "sample_id",
        "r1",
        "r2",
    ]

    assert len(table) == 1

    assert table.loc[
        0,
        "sample_id",
    ] == "sample_001"

    assert table.loc[
        0,
        "r1",
    ] == str(
        r1_path.resolve()
    )

    assert table.loc[
        0,
        "r2",
    ] == str(
        r2_path.resolve()
    )


def test_construct_manifest_missing_r2_raises(
        tmp_path: Path,
):
    """Confirm incomplete FASTQ pairs raise an error."""
    create_fastq(
        tmp_path
        / "sample_001_R1.fastq.gz"
    )

    with pytest.raises(
            ValueError,
            match="expected exactly one R2",
    ):
        construct_manifest_from_directory(
            tmp_path
        )


def test_read_source_manifest_xlsx(
        tmp_path: Path,
):
    """Confirm Excel source manifests are supported."""
    manifest_path = (
        tmp_path
        / "samples.xlsx"
    )

    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "r1": "sample_001_R1.fastq.gz",
                "r2": "sample_001_R2.fastq.gz",
            }
        ]
    ).to_excel(
        manifest_path,
        index=False,
    )

    table = read_source_manifest(
        manifest_path
    )

    assert table.loc[
        0,
        "sample_id",
    ] == "sample_001"


def test_load_source_manifest_row_per_sample(
        tmp_path: Path,
):
    """Confirm a filename-only source manifest is normalized."""
    reads_directory = (
        tmp_path
        / "reads"
    )

    r1_path = create_fastq(
        reads_directory
        / "sample_001_R1.fastq.gz"
    )

    r2_path = create_fastq(
        reads_directory
        / "sample_001_R2.fastq.gz"
    )

    manifest_path = (
        tmp_path
        / "samples.tsv"
    )

    manifest_path.write_text(
        (
            "sample_id\tr1\tr2\tspecies\n"
            "sample_001\t"
            "sample_001_R1.fastq.gz\t"
            "sample_001_R2.fastq.gz\t"
            "atromaculatus\n"
        ),
        encoding="utf-8",
    )

    table = load_source_manifest(
        manifest_path=manifest_path,
        input_directory=reads_directory,
    )

    assert table.loc[
        0,
        "r1",
    ] == str(r1_path.resolve())

    assert table.loc[
        0,
        "r2",
    ] == str(r2_path.resolve())


def test_prepare_runtime_manifest_from_source(
        tmp_path: Path,
):
    """Confirm source manifests are copied into runtime form."""
    reads_directory = (
        tmp_path
        / "reads"
    )

    create_fastq(
        reads_directory
        / "sample_001_R1.fastq.gz"
    )

    create_fastq(
        reads_directory
        / "sample_001_R2.fastq.gz"
    )

    source_manifest = (
        tmp_path
        / "samples.tsv"
    )

    source_manifest.write_text(
        (
            "sample_id\tr1\tr2\n"
            "sample_001\t"
            "sample_001_R1.fastq.gz\t"
            "sample_001_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )

    runtime_manifest = (
        tmp_path
        / "job"
        / "metadata"
        / "runtime_manifest.tsv"
    )

    table = prepare_runtime_manifest(
        output_path=runtime_manifest,
        source_manifest=source_manifest,
        input_directory=reads_directory,
    )

    assert runtime_manifest.exists()

    written_table = pd.read_csv(
        runtime_manifest,
        sep="\t",
    )

    assert written_table[
        "sample_id"
    ].tolist() == [
        "sample_001",
    ]

    assert table.index.tolist() == [
        "sample_001",
    ]


def test_prepare_runtime_manifest_from_directory(
        tmp_path: Path,
):
    """Confirm manifest-free discovery writes runtime manifest."""
    input_directory = (
        tmp_path
        / "reads"
    )

    create_fastq(
        input_directory
        / "sample_001_R1.fastq.gz"
    )

    create_fastq(
        input_directory
        / "sample_001_R2.fastq.gz"
    )

    runtime_manifest = (
        tmp_path
        / "job"
        / "metadata"
        / "runtime_manifest.tsv"
    )

    table = prepare_runtime_manifest(
        output_path=runtime_manifest,
        input_directory=input_directory,
    )

    assert runtime_manifest.exists()
    assert table.index.tolist() == [
        "sample_001",
    ]


def test_prepare_runtime_manifest_without_input_directory_raises(
        tmp_path: Path,
):
    """Confirm input_directory is always required."""
    with pytest.raises(
            ValueError,
            match="input_directory",
    ):
        prepare_runtime_manifest(
            output_path=(
                tmp_path
                / "runtime_manifest.tsv"
            ),
            input_directory=None,
        )
