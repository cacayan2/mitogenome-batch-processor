"""Execution layer for selecting and taxonomically enriching BLAST hits."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.blast_stats import (
    parse_blast_tsv,
    select_top_blast_matches,
    write_top_blast_matches,
)
from mitopipeline.stats.blast_taxonomy import (
    enrich_blast_scientific_names,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Select top BLAST matches and resolve missing scientific names."
        )
    )
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--blast-results", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--maximum-matches", type=int, default=6)
    parser.add_argument("--entrez-email", required=True)
    parser.add_argument("--entrez-api-key", default=None)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def main() -> int:
    """Parse, rank, enrich, and write top BLAST matches."""
    logger = None

    try:
        args = parse_args()
        logger = make_logger(
            name="blast_hits",
            log_file_path=args.log_file,
        )

        logger.info(
            "Selecting top BLAST matches for sample %s.",
            args.sample_id,
        )

        matches = parse_blast_tsv(
            blast_path=Path(args.blast_results),
            logger=logger,
        )
        selected_matches = select_top_blast_matches(
            matches=matches,
            maximum_matches=args.maximum_matches,
            logger=logger,
        )
        selected_matches = enrich_blast_scientific_names(
            matches=selected_matches,
            entrez_email=args.entrez_email,
            entrez_api_key=args.entrez_api_key,
            logger=logger,
        )

        write_top_blast_matches(
            matches=selected_matches,
            output_path=Path(args.output_file),
            sample_id=args.sample_id,
            logger=logger,
        )

        if len(selected_matches) < args.maximum_matches:
            logger.warning(
                "Only %d unique BLAST matches were available for %s; "
                "%d were requested.",
                len(selected_matches),
                args.sample_id,
                args.maximum_matches,
            )

        logger.info(
            "Selected and enriched %d BLAST matches for sample %s.",
            len(selected_matches),
            args.sample_id,
        )
        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                "BLAST match selection failed: %s",
                error,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
