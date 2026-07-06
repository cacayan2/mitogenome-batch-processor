"""run_phylogeny_alignment.py

Execution layer for aligning phylogenetic sequence datasets.
"""

# Imports
import argparse
import subprocess
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.phylogeny_stats import (
    read_phylogeny_dataset,
    validate_alignment,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Align an assembled mitochondrial genome and its six "
            "selected BLAST references with MAFFT."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
    )

    parser.add_argument(
        "--input-fasta",
        required=True,
    )

    parser.add_argument(
        "--output-fasta",
        required=True,
    )

    parser.add_argument(
        "--mafft-bin",
        default="mafft",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def run_phylogeny_alignment(
        input_fasta: str | Path,
        output_fasta: str | Path,
        mafft_bin: str,
        threads: int,
        logger,
) -> None:
    """Run MAFFT on a seven-sequence phylogenetic dataset.

    Args:
        input_fasta (str | Path): Unaligned FASTA.
        output_fasta (str | Path): Aligned FASTA output.
        mafft_bin (str): MAFFT executable.
        threads (int): Thread count.
        logger: Execution logger.
    """
    if threads <= 0:
        raise ValueError(
            "MAFFT threads must be greater than zero."
        )

    input_fasta = Path(input_fasta)
    output_fasta = Path(output_fasta)

    read_phylogeny_dataset(
        fasta_path=input_fasta,
        expected_reference_count=6,
        logger=logger,
    )

    output_fasta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        mafft_bin,
        "--auto",
        "--nuc",
        "--thread",
        str(threads),
        str(input_fasta),
    ]

    logger.info(
        "Running MAFFT command: "
        + " ".join(command)
    )

    with output_fasta.open(
            "w",
            encoding="utf-8",
    ) as output_handle:
        result = subprocess.run(
            command,
            stdout=output_handle,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    if result.stderr:
        logger.info(
            result.stderr.strip()
        )

    if result.returncode != 0:
        output_fasta.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            f"MAFFT failed with exit code {result.returncode}."
        )

    validate_alignment(
        alignment_path=output_fasta,
        expected_sequence_count=7,
        logger=logger,
    )


def main() -> int:
    """Run MAFFT alignment.

    Returns:
        int: Exit code.
    """
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="phylogeny_alignment",
            log_file_path=args.log_file,
        )

        logger.info(
            f"Starting phylogenetic alignment for "
            f"sample {args.sample_id}."
        )

        run_phylogeny_alignment(
            input_fasta=args.input_fasta,
            output_fasta=args.output_fasta,
            mafft_bin=args.mafft_bin,
            threads=args.threads,
            logger=logger,
        )

        logger.info(
            f"Completed phylogenetic alignment for "
            f"sample {args.sample_id}."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"Phylogenetic alignment failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())