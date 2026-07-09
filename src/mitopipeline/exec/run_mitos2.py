"""run_mitos2.py

Execution script for running MITOS2 annotation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.mitos2 import MITOS2Runner
from mitopipeline.logging.logger_factory import make_logger


def parse_bool(value: str) -> bool:
    """Parse a string boolean value."""
    normalized = value.strip().lower()

    if normalized in {"true", "1", "yes", "y"}:
        return True

    if normalized in {"false", "0", "no", "n"}:
        return False

    raise ValueError(f"Cannot parse boolean value: {value}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run MITOS2 annotation.")
    parser.add_argument(
        "--conda-env",
        default="mito-annotation",
        help="Conda environment containing MITOS2.",
    )
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--genetic-code", type=int, required=True)
    parser.add_argument("--refseqver", required=True)
    parser.add_argument("--refdir", required=True)
    parser.add_argument("--linear", action="store_true")
    parser.add_argument("--zip-output", action="store_true")
    parser.add_argument("--circular", required=True)
    parser.add_argument("--noplots", required=True)
    parser.add_argument("--best", required=True)
    parser.add_argument("--ncbicode", required=True)
    return parser.parse_args()


def main() -> int:
    """Run MITOS2 annotation."""
    args = parse_args()

    Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = make_logger(
        name=f"mitos2.{args.sample_id}",
        log_file_path=args.log_file,
    )

    logger.info(
        f"Starting MITOS2 annotation for sample {args.sample_id}."
    )

    try:
        runner = MITOS2Runner(
            input_fasta=Path(args.input_fasta).resolve(),
            output_dir=Path(args.output_dir).resolve(),
            working_dir=Path(args.working_dir).resolve(),
            conda_env=args.conda_env,
            genetic_code=args.genetic_code,
            refseqver=args.refseqver,
            refdir=Path(args.refdir).resolve(),
            circular=parse_bool(args.circular),
            noplots=parse_bool(args.noplots),
            zip_output=args.zip_output,
            best=parse_bool(args.best),
            ncbicode=parse_bool(args.ncbicode),
            logger=logger,
        )

        result = runner.run()

        if not result.success:
            logger.error(
                f"MITOS2 external command failed for sample "
                f"{args.sample_id}."
            )
            logger.debug(f"MITOS2 return code: {result.return_code}")
            logger.debug(f"MITOS2 stdout:\n{result.stdout}")
            logger.debug(f"MITOS2 stderr:\n{result.stderr}")
            return result.return_code or 1

        logger.info(
            f"MITOS2 annotation completed for sample {args.sample_id}."
        )
        return 0

    except Exception as error:
        logger.exception(
            f"MITOS2 annotation failed for sample {args.sample_id}: "
            f"{error}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
