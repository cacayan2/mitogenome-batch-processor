"""test_report_data.py

Unit tests for report-data aggregation.
"""

# Imports
import json
from pathlib import Path

from mitopipeline.reporting.report_data import (
    collect_sample_report_data,
    read_sample_metadata,
)


def create_report_outputs(
        job_directory: Path,
) -> None:
    """Create minimal canonical pipeline outputs."""
    (
        job_directory
        / "metadata"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "trimming"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "assembly"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "annotation"
        / "sample_001"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "phylogeny"
        / "blast"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "phylogeny"
        / "iqtree"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "phylogeny"
        / "trees"
    ).mkdir(
        parents=True
    )

    (
        job_directory
        / "metadata"
        / "runtime_manifest.tsv"
    ).write_text(
        (
            "sample_id\tr1\tr2\tspecies\n"
            "sample_001\t/a_R1.fastq.gz\t"
            "/a_R2.fastq.gz\tSpecies one\n"
        ),
        encoding="utf-8",
    )

    fastp_data = {
        "summary": {
            "before_filtering": {
                "total_reads": 100,
                "total_bases": 10000,
                "q20_rate": 0.95,
                "q30_rate": 0.90,
                "gc_content": 0.42,
            },
            "after_filtering": {
                "total_reads": 80,
                "total_bases": 7600,
                "q20_rate": 0.98,
                "q30_rate": 0.94,
                "gc_content": 0.41,
            },
        },
        "filtering_result": {
            "passed_filter_reads": 80,
            "low_quality_reads": 10,
            "too_many_N_reads": 2,
            "too_short_reads": 8,
            "too_long_reads": 0,
        },
        "adapter_cutting": {
            "adapter_trimmed_reads": 20,
            "adapter_trimmed_bases": 200,
        },
    }

    (
        job_directory
        / "trimming"
        / "sample_001.fastp.json"
    ).write_text(
        json.dumps(
            fastp_data
        ),
        encoding="utf-8",
    )

    (
        job_directory
        / "assembly"
        / "sample_001.fasta"
    ).write_text(
        ">mitogenome\nATGCGCATGC\n",
        encoding="utf-8",
    )

    (
        job_directory
        / "annotation"
        / "sample_001"
        / "result.gff"
    ).write_text(
        (
            "##gff-version 3\n"
            "mito\tMITOS2\tgene\t1\t9\t.\t+\t.\t"
            "ID=gene1;Name=cox1\n"
        ),
        encoding="utf-8",
    )

    (
        job_directory
        / "phylogeny"
        / "blast"
        / "sample_001.top_hits.tsv"
    ).write_text(
        (
            "sample_id\trank\tqseqid\tsseqid\tpident\t"
            "length\tmismatch\tgapopen\tqstart\tqend\t"
            "sstart\tsend\tevalue\tbitscore\tqcovs\t"
            "staxids\tsscinames\tstitle\n"
            "sample_001\t1\tquery\tNC_001.1\t99.5\t"
            "9\t0\t0\t1\t9\t1\t9\t0.0\t100\t100\t"
            "123\tSpecies one\tSpecies one mitochondrion\n"
        ),
        encoding="utf-8",
    )

    (
        job_directory
        / "phylogeny"
        / "iqtree"
        / "sample_001.maximum_likelihood.iqtree"
    ).write_text(
        "Best-fit model according to BIC: GTR+F+I+G4\n",
        encoding="utf-8",
    )

    (
        job_directory
        / "phylogeny"
        / "trees"
        / "sample_001.maximum_likelihood.nwk"
    ).write_text(
        (
            "("
            "sample_001|assembled:0.1,"
            "reference_01|A|Species_1:0.1,"
            "reference_02|B|Species_2:0.1,"
            "reference_03|C|Species_3:0.1,"
            "reference_04|D|Species_4:0.1,"
            "reference_05|E|Species_5:0.1,"
            "reference_06|F|Species_6:0.1"
            ");"
        ),
        encoding="utf-8",
    )


def test_read_sample_metadata(
        tmp_path: Path,
):
    """Confirm one runtime-manifest row is returned."""
    manifest_path = (
        tmp_path
        / "runtime_manifest.tsv"
    )

    manifest_path.write_text(
        (
            "sample_id\tr1\tr2\tspecies\n"
            "sample_001\t/a\t/b\tSpecies one\n"
        ),
        encoding="utf-8",
    )

    metadata = read_sample_metadata(
        runtime_manifest_path=manifest_path,
        sample_id="sample_001",
    )

    assert metadata["species"] == "Species one"


def test_collect_sample_report_data(
        tmp_path: Path,
):
    """Confirm canonical parsers are aggregated."""
    job_directory = (
        tmp_path
        / "job"
    )

    create_report_outputs(
        job_directory
    )

    report_data = collect_sample_report_data(
        sample_id="sample_001",
        job_directory=job_directory,
    )

    assert (
        report_data.metadata["species"]
        == "Species one"
    )

    assert (
        report_data.fastp_stats["reads_in"]
        == 100
    )

    assert (
        report_data.assembly_stats[
            "total_length_bp"
        ]
        == 10
    )

    assert (
        report_data.annotation_stats[
            "total_features"
        ]
        == 1
    )

    assert (
        report_data.blast_matches[0][
            "sseqid"
        ]
        == "NC_001.1"
    )

    assert (
        report_data.phylogeny_model
        == "GTR+F+I+G4"
    )

    assert report_data.phylogeny_tip_count == 7