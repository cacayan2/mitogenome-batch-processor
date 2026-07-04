"""run_blast.py

Execution layer connecting BLAST to Snakemake.
"""

# Imports
import argparse
from logging import Logger
from pathlib import Path

from mitopipeline.api.blast import BlastRunner, DEFAULT_OUTFMT
from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run local nucleotide BLAST on one assembled mitochondrial genome."
        )
    )

    # Required arguments.
    parser.add_argument(
        "--sample-id",
        required=True,
        help="Unique sample identifier.",
    )
    parser.add_argument(
        "--query-fasta",
        required=True,
        help="Path to assembled mitochondrial genome FASTA.",
    )
    parser.add_argument(
        "--database",
        required=True,
        help="Prefix of the local nucleotide BLAST database.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for BLAST output.",
    )
    parser.add_argument(
        "--working-dir",
        required=True,
        help="Working directory for BLAST execution.",
    )
    parser.add_argument(
        "--threads",
        required=True,
        type=int,
        help="Number of CPU threads.",
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to BLAST log file.",
    )

    # Optional BLAST arguments.
    parser.add_argument(
        "--task",
        default="blastn",
        choices=[
            "blastn",
            "megablast",
            "dc-megablast",
            "blastn-short",
        ],
        help="BLAST nucleotide search task.",
    )
    parser.add_argument(
        "--output-format",
        default=DEFAULT_OUTFMT,
        help="BLAST output format string.",
    )
    parser.add_argument(
        "--evalue",
        type=float,
        default=1e-5,
        help="Maximum expected value.",
    )
    parser.add_argument(
        "--max-target-seqs",
        type=int,
        default=10,
        help="Maximum number of target sequences retained.",
    )
    parser.add_argument(
        "--max-hsps",
        type=int,
        default=1,
        help="Maximum number of HSPs per query-subject pair.",
    )
    parser.add_argument(
        "--perc-identity",
        type=float,
        default=None,
        help="Minimum percent identity.",
    )
    parser.add_argument(
        "--query-coverage",
        type=float,
        default=None,
        help="Minimum HSP query coverage percentage.",
    )
    parser.add_argument(
        "--word-size",
        type=int,
        default=None,
        help="BLAST word size.",
    )

    return parser.parse_args()


def build_logger(args: argparse.Namespace) -> Logger:
    """Construct BLAST logger.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Logger: Configured logger.
    """
    return make_logger(
        name="blast",
        log_file_path=args.log_file,
    )


def main() -> int:
    """Run BLAST for one mitochondrial genome.

    Returns:
        int: Process exit code.
    """
    logger = None

    try:
        args = parse_args()
        logger = build_logger(args)

        logger.info(
            f"Starting BLAST execution for sample {args.sample_id}."
        )

        runner = BlastRunner(
            query_fasta=Path(args.query_fasta),
            database=Path(args.database),
            output_dir=Path(args.output_dir),
            working_dir=Path(args.working_dir),
            sample_id=args.sample_id,
            threads=args.threads,
            task=args.task,
            output_format=args.output_format,
            evalue=args.evalue,
            max_target_seqs=args.max_target_seqs,
            max_hsps=args.max_hsps,
            perc_identity=args.perc_identity,
            query_coverage=args.query_coverage,
            word_size=args.word_size,
            logger=logger,
        )

        result = runner.run()

        if not result.success:
            logger.error(
                f"BLAST execution failed for sample {args.sample_id}."
            )
            logger.debug(
                f"BLAST return code: {result.return_code}"
            )
            logger.debug(
                f"BLAST stdout: {result.stdout}"
            )
            logger.debug(
                f"BLAST stderr: {result.stderr}"
            )

            return result.return_code if result.return_code != 0 else 1

        logger.info(
            f"BLAST execution completed for sample {args.sample_id}."
        )
        logger.debug(
            f"BLAST runtime seconds: {result.runtime_seconds}"
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"BLAST execution failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())