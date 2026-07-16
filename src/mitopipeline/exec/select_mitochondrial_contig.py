"""Assess a GetOrganelle assembly and select its primary mtDNA contig."""

from __future__ import annotations

import argparse
from pathlib import Path

from Bio import SeqIO

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.mitochondrial_contig import (
    assess_mitochondrial_assembly,
    write_assessment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--assembly-fasta", required=True)
    parser.add_argument("--top-hits", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--fragments-fasta", required=True)
    parser.add_argument("--assessment-json", required=True)
    parser.add_argument("--complete-min-length", type=int, default=14_000)
    parser.add_argument("--complete-max-length", type=int, default=22_000)
    parser.add_argument("--minimum-fragment-length", type=int, default=200)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = make_logger(
        f"select_mitochondrial_contig.{args.sample_id}",
        args.log_file,
    )

    try:
        assessment, primary, mitochondrial_records = (
            assess_mitochondrial_assembly(
                assembly_fasta=args.assembly_fasta,
                top_hits_tsv=args.top_hits,
                complete_min_length=args.complete_min_length,
                complete_max_length=args.complete_max_length,
                minimum_fragment_length=args.minimum_fragment_length,
            )
        )

        output_fasta = Path(args.output_fasta)
        fragments_fasta = Path(args.fragments_fasta)
        output_fasta.parent.mkdir(parents=True, exist_ok=True)
        fragments_fasta.parent.mkdir(parents=True, exist_ok=True)

        if SeqIO.write([primary], output_fasta, "fasta") != 1:
            raise RuntimeError("Failed to write the primary mitochondrial contig")
        if not SeqIO.write(mitochondrial_records, fragments_fasta, "fasta"):
            raise RuntimeError("Failed to write mitochondrial fragments")

        write_assessment(assessment, args.assessment_json)

        logger.info(
            "Assembly status=%s; primary=%s (%d bp); "
            "mitochondrial scaffolds=%d; combined length=%d bp.",
            assessment.status,
            assessment.primary_contig_id,
            assessment.primary_contig_length,
            assessment.mitochondrial_contig_count,
            assessment.mitochondrial_total_length,
        )
        logger.info("Assessment reason: %s", assessment.reason)
        return 0

    except Exception as error:
        logger.exception(
            "Mitochondrial assembly assessment failed for %s: %s",
            args.sample_id,
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
