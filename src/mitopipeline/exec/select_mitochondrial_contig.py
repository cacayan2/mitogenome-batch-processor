"""Execution script for selecting a mitochondrial assembly contig."""

from __future__ import annotations

import argparse

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.mitochondrial_contig import (
    select_mitochondrial_contig,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--assembly-fasta", required=True)
    parser.add_argument("--top-hits", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--log-file", required=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logger = make_logger(
        f"select_mitochondrial_contig.{args.sample_id}",
        args.log_file,
    )

    logger.info(
        "Selecting mitochondrial contig for sample %s.",
        args.sample_id,
    )

    try:
        selected_record = select_mitochondrial_contig(
            assembly_fasta=args.assembly_fasta,
            top_hits_tsv=args.top_hits,
            output_fasta=args.output_fasta,
        )

        logger.info(
            "Selected contig %s containing %d bases.",
            selected_record.id,
            len(selected_record.seq),
        )

        return 0

    except Exception as error:
        logger.exception(
            "Mitochondrial-contig selection failed for sample %s: %s",
            args.sample_id,
            error,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())