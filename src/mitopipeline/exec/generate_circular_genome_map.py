"""generate_circular_genome_map.py

Execution layer for circular mitochondrial genome visualization.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import (
    make_logger,
)
from mitopipeline.visualization.circular_map import (
    render_circular_genome_map,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate publication-ready circular mitochondrial "
            "genome maps from MITOS2 result.gff and result.fas."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
    )

    parser.add_argument(
        "--gff",
        required=True,
    )

    parser.add_argument(
        "--fasta",
        required=True,
    )

    parser.add_argument(
        "--output-png",
        required=True,
    )

    parser.add_argument(
        "--output-svg",
        required=True,
    )

    parser.add_argument(
        "--output-pdf",
        required=True,
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Generate circular mitochondrial genome map outputs."""
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="visualization",
            log_file_path=args.log_file,
        )

        logger.info(
            f"Generating circular genome map for "
            f"{args.sample_id}."
        )

        render_circular_genome_map(
            sample_id=args.sample_id,
            gff_path=Path(
                args.gff
            ),
            fasta_path=Path(
                args.fasta
            ),
            output_png=Path(
                args.output_png
            ),
            output_svg=Path(
                args.output_svg
            ),
            output_pdf=Path(
                args.output_pdf
            ),
            dpi=args.dpi,
            logger=logger,
        )

        logger.info(
            f"Completed circular genome map for "
            f"{args.sample_id}."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Circular genome map generation failed: "
                f"{error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
