"""generate_alignment_dataset.py

Execution layer for generating combined phylogenetic FASTA datasets.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.alignment_dataset import (
    generate_alignment_dataset,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a phylogenetic FASTA dataset containing "
            "an assembled genome and selected BLAST references."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
        help="Pipeline sample identifier.",
    )

    parser.add_argument(
        "--assembly-fasta",
        required=True,
        help="Path to assembled-genome FASTA.",
    )

    parser.add_argument(
        "--top-hits",
        required=True,
        help="Path to selected BLAST-hit TSV.",
    )

    parser.add_argument(
        "--output-fasta",
        required=True,
        help="Path to combined FASTA output.",
    )

    parser.add_argument(
        "--entrez-email",
        required=True,
        help="Email address used for NCBI Entrez requests.",
    )

    parser.add_argument(
        "--entrez-api-key",
        default=None,
        help="Optional NCBI Entrez API key.",
    )

    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to execution log.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate a combined phylogenetic FASTA dataset.

    Returns:
        int: Exit code.
    """
    # Initializing logger.
    logger = None

    try:
        # Parsing arguments.
        args = parse_args()

        # Creating logger.
        logger = make_logger(
            name="alignment_dataset",
            log_file_path=args.log_file,
        )

        # Logging start.
        logger.info(
            f"Starting alignment-dataset generation for "
            f"sample {args.sample_id}."
        )

        # Generating dataset.
        generate_alignment_dataset(
            sample_id=args.sample_id,
            assembly_fasta=Path(
                args.assembly_fasta
            ),
            top_hits_tsv=Path(
                args.top_hits
            ),
            output_fasta=Path(
                args.output_fasta
            ),
            entrez_email=args.entrez_email,
            entrez_api_key=args.entrez_api_key,
            logger=logger,
        )

        # Logging completion.
        logger.info(
            f"Completed alignment-dataset generation for "
            f"sample {args.sample_id}."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Alignment-dataset generation failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())