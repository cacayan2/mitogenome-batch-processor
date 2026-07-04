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
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run local or remote nucleotide BLAST."
    )

    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--query-fasta", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--mode", required=True, choices=["local", "remote"])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--threads", required=True, type=int)
    parser.add_argument("--log-file", required=True)

    parser.add_argument(
        "--task",
        default="blastn",
        choices=[
            "blastn",
            "megablast",
            "dc-megablast",
            "blastn-short",
        ],
    )
    parser.add_argument(
        "--output-format",
        default=DEFAULT_OUTFMT,
    )
    parser.add_argument(
        "--evalue",
        type=float,
        default=1e-5,
    )
    parser.add_argument(
        "--max-target-seqs",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--max-hsps",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--perc-identity",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--query-coverage",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--word-size",
        type=int,
        default=None,
    )

    return parser.parse_args()


def build_logger(
    args: argparse.Namespace,
) -> Logger:
    """Construct BLAST logger."""
    return make_logger(
        name="blast",
        log_file_path=args.log_file,
    )


def main() -> int:
    """Run BLAST for one sample."""
    logger = None

    try:
        args = parse_args()
        logger = build_logger(args)

        runner = BlastRunner(
            query_fasta=Path(args.query_fasta),
            database=args.database,
            output_dir=Path(args.output_dir),
            working_dir=Path(args.working_dir),
            sample_id=args.sample_id,
            mode=args.mode,
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
                f"BLAST failed for sample {args.sample_id}."
            )

            return (
                result.return_code
                if result.return_code != 0
                else 1
            )

        logger.info(
            f"BLAST completed for sample {args.sample_id}."
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