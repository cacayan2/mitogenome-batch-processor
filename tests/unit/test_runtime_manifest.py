"""test_runtime_manifest.py

Unit tests for runtime-manifest normalization and FASTQ discovery.
"""

# Imports
from pathlib import Path

import pandas as pd
import pytest

from mitopipeline.config.runtime_manifest import (
    construct_manifest_from_directory,
    load_source_manifest,
    parse_fastq_filename,
    prepare_runtime_manifest,
)


def touch_fastq(
        path: Path,
) -> Path:
    """Create an empty FASTQ fixture file.

    Args:
        path (Path): FASTQ output path.

    Returns:
        Path: Created path.
    """
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.touch()

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


def test_load_source_manifest(
        tmp_path: Path,
):
    """Confirm a source manifest is normalized."""
    reads_directory = (
        tmp_path
        / "reads"
    )

    r1_path = touch_fastq(
        reads_directory
        / "sample_001_R1.fastq.gz"
    )

    r2_path = touch_fastq(
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
            "reads/sample_001_R1.fastq.gz\t"
            "reads/sample_001_R2.fastq.gz\t"
            "Species one\n"
        ),
        encoding="utf-8",
    )

    table = load_source_manifest(
        manifest_path
    )

    assert list(
        table.columns
    ) == [
        "sample_id",
        "r1",
        "r2",
        "species",
    ]

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

    assert table.loc[
        0,
        "species",
    ] == "Species one"


def test_construct_manifest_from_directory(
        tmp_path: Path,
):
    """Confirm paired FASTQs generate a minimal manifest."""
    r1_path = touch_fastq(
        tmp_path
        / "nested"
        / "sample_001_R1.fastq.gz"
    )

    r2_path = touch_fastq(
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


def test_construct_manifest_multiple_samples(
        tmp_path: Path,
):
    """Confirm multiple FASTQ pairs generate multiple rows."""
    for sample_id in (
        "sample_001",
        "sample_002",
    ):
        touch_fastq(
            tmp_path
            / f"{sample_id}_R1.fastq.gz"
        )

        touch_fastq(
            tmp_path
            / f"{sample_id}_R2.fastq.gz"
        )

    table = construct_manifest_from_directory(
        tmp_path
    )

    assert table[
        "sample_id"
    ].tolist() == [
        "sample_001",
        "sample_002",
    ]


def test_construct_manifest_missing_r2_raises(
        tmp_path: Path,
):
    """Confirm incomplete FASTQ pairs raise an error."""
    touch_fastq(
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


def test_construct_manifest_duplicate_r1_raises(
        tmp_path: Path,
):
    """Confirm ambiguous duplicate mates raise an error."""
    touch_fastq(
        tmp_path
        / "directory_a"
        / "sample_001_R1.fastq.gz"
    )

    touch_fastq(
        tmp_path
        / "directory_b"
        / "sample_001_R1.fastq.gz"
    )

    touch_fastq(
        tmp_path
        / "sample_001_R2.fastq.gz"
    )

    with pytest.raises(
            ValueError,
            match="expected exactly one R1",
    ):
        construct_manifest_from_directory(
            tmp_path
        )


def test_prepare_runtime_manifest_from_source(
        tmp_path: Path,
):
    """Confirm source manifests are copied into runtime form."""
    reads_directory = (
        tmp_path
        / "reads"
    )

    touch_fastq(
        reads_directory
        / "sample_001_R1.fastq.gz"
    )

    touch_fastq(
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
            "reads/sample_001_R1.fastq.gz\t"
            "reads/sample_001_R2.fastq.gz\n"
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

    touch_fastq(
        input_directory
        / "sample_001_R1.fastq.gz"
    )

    touch_fastq(
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

    assert table.loc[
        "sample_001",
        "r1",
    ].endswith(
        "sample_001_R1.fastq.gz"
    )


def test_prepare_runtime_manifest_prefers_source_manifest(
        tmp_path: Path,
):
    """Confirm a source manifest takes precedence over discovery."""
    manifest_reads = (
        tmp_path
        / "manifest_reads"
    )

    discovered_reads = (
        tmp_path
        / "discovered_reads"
    )

    touch_fastq(
        manifest_reads
        / "manifest_sample_R1.fastq.gz"
    )

    touch_fastq(
        manifest_reads
        / "manifest_sample_R2.fastq.gz"
    )

    touch_fastq(
        discovered_reads
        / "discovered_sample_R1.fastq.gz"
    )

    touch_fastq(
        discovered_reads
        / "discovered_sample_R2.fastq.gz"
    )

    source_manifest = (
        tmp_path
        / "samples.tsv"
    )

    source_manifest.write_text(
        (
            "sample_id\tr1\tr2\n"
            "manifest_sample\t"
            "manifest_reads/"
            "manifest_sample_R1.fastq.gz\t"
            "manifest_reads/"
            "manifest_sample_R2.fastq.gz\n"
        ),
        encoding="utf-8",
    )

    table = prepare_runtime_manifest(
        output_path=(
            tmp_path
            / "runtime_manifest.tsv"
        ),
        source_manifest=source_manifest,
        input_directory=discovered_reads,
    )

    assert table.index.tolist() == [
        "manifest_sample",
    ]


def test_prepare_runtime_manifest_without_source_raises(
        tmp_path: Path,
):
    """Confirm at least one input source is required."""
    with pytest.raises(
            ValueError,
            match="Either 'manifest' or 'input_directory'",
    ):
        prepare_runtime_manifest(
            output_path=(
                tmp_path
                / "runtime_manifest.tsv"
            ),
        )