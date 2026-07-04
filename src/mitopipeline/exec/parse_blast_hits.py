"""parse_blast_hits.py

Execution layer for selecting top BLAST matches.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.blast_stats import (
    parse_blast_tsv,
    select_top_blast_matches,
    write_top_blast_matches,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Select top BLAST matches for phylogenetic validation."
    )

    parser.add_argument(
        "--sample-id",
        required=True,
        help="Pipeline sample identifier.",
    )
    parser.add_argument(
        "--blast-results",
        required=True,
        help="Path to BLAST TSV results.",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Path to the selected-hit TSV output.",
    )
    parser.add_argument(
        "--maximum-matches",
        type=int,
        default=6,
        help="Maximum number of unique BLAST matches retained.",
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to execution log.",
    )

    return parser.parse_args()


def main() -> int:
    """Parse, rank, and write top BLAST matches.

    Returns:
        int: Exit code.
    """
    # Initializing logger.
    logger = None

    try:
        # Parsing command-line arguments.
        args = parse_args()

        # Constructing logger.
        logger = make_logger(
            name="blast_hits",
            log_file_path=args.log_file,
        )

        # Logging start.
        logger.info(
            f"Selecting top BLAST matches for sample {args.sample_id}."
        )

        # Parsing BLAST TSV.
        matches = parse_blast_tsv(
            blast_path=Path(args.blast_results),
            logger=logger,
        )

        # Selecting top BLAST matches.
        selected_matches = select_top_blast_matches(
            matches=matches,
            maximum_matches=args.maximum_matches,
        )

        # Writing top BLAST matches.
        write_top_blast_matches(
            matches=selected_matches,
            output_path=Path(args.output_file),
            sample_id=args.sample_id,
            logger=logger,
        )

        # Logging end warnings.
        if len(selected_matches) < args.maximum_matches:
            logger.warning(
                f"Only {len(selected_matches)} unique BLAST matches were "
                f"available for sample {args.sample_id}; "
                f"{args.maximum_matches} were requested."
            )

        # Logging end.
        logger.info(
            f"Selected {len(selected_matches)} BLAST matches for "
            f"sample {args.sample_id}."
        )

        # Returning success.
        return 0

    # Exception handling.
    except Exception as error:
        # Logging error.
        if logger is not None:
            logger.exception(
                f"BLAST match selection failed: {error}"
            )
        # Returning failure.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())