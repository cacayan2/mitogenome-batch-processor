"""render_phylogeny.py

Execution layer for rendering and documenting phylogenetic trees.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.phylogeny_stats import (
    render_phylogenetic_tree,
    write_phylogeny_summary,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Render an IQ-TREE phylogeny as publication-ready "
            "vector and raster figures."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
    )

    parser.add_argument(
        "--alignment",
        required=True,
    )

    parser.add_argument(
        "--input-newick",
        required=True,
    )

    parser.add_argument(
        "--iqtree-report",
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
        "--output-png",
        required=True,
    )

    parser.add_argument(
        "--output-summary",
        required=True,
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
    )

    parser.add_argument(
        "--ultrafast-bootstrap",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--sh-alrt",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--midpoint-root",
        action="store_true",
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def main() -> int:
    """Render and document the phylogeny.

    Returns:
        int: Exit code.
    """
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="phylogeny_render",
            log_file_path=args.log_file,
        )

        render_phylogenetic_tree(
            tree_path=Path(
                args.input_newick
            ),
            output_svg=Path(
                args.output_svg
            ),
            output_pdf=Path(
                args.output_pdf
            ),
            output_png=Path(
                args.output_png
            ),
            title=(
                f"{args.sample_id} mitochondrial "
                "maximum-likelihood phylogeny"
            ),
            dpi=args.dpi,
            midpoint_root=args.midpoint_root,
            logger=logger,
        )

        write_phylogeny_summary(
            sample_id=args.sample_id,
            alignment_path=Path(
                args.alignment
            ),
            tree_path=Path(
                args.input_newick
            ),
            report_path=Path(
                args.iqtree_report
            ),
            output_path=Path(
                args.output_summary
            ),
            ultrafast_bootstrap=args.ultrafast_bootstrap,
            sh_alrt=args.sh_alrt,
            midpoint_root_figure=args.midpoint_root,
            logger=logger,
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Phylogeny rendering failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())