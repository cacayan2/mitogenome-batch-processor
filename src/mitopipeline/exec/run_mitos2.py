"""run_mitos2.py

Execution script for running MITOS2 annotation.
"""

# Imports
import argparse
from pathlib import Path

from mitopipeline.api.mitos2 import MITOS2Runner
from mitopipeline.logging.logger_factory import make_logger


def parse_bool(value: str) -> bool:
    """Parse a string boolean value.
    
    Args:
        value (str): String value to parse.
    
    Returns:
        bool: Parsed boolean value.
    """

    # Stripping whitespace and converting to lowercase.
    value = value.strip().lower()

    # Returning boolean value.
    if value in {"true", "1", "yes", "y"}:
        return True

    if value in {"false", "0", "no", "n"}:
        return False

    # Raising error if value is not a boolean.
    raise ValueError(f"Cannot parse boolean value: {value}")

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    # Initializing parser.
    parser = argparse.ArgumentParser(description="Run MITOS2 annotation.")

    # Adding conda environment argument.
    parser.add_argument("--conda-env", default="mito-annotation", help="Conda environment containing MITOS2.")

    # Adding required arguments.
    parser.add_argument("--sample-id", required=True, help="Sample ID.")
    parser.add_argument("--input-fasta", required=True, help="Input assembly FASTA.")
    parser.add_argument("--output-dir", required=True, help="MITOS2 output directory.")
    parser.add_argument("--working-dir", required=True, help="Working directory.")
    parser.add_argument("--log-file", required=True, help="Log file path.")
    parser.add_argument("--genetic-code", type=int, required=True, help="MITOS2 genetic code.")
    parser.add_argument("--refseqver", required=True, help="MITOS2 reference version.")
    parser.add_argument("--refdir", required=True, help="MITOS2 reference root directory.")

    # Adding optional flags.
    parser.add_argument("--linear", action="store_true", help="Treat genome as linear.")
    parser.add_argument("--zip-output", action="store_true", help="Create zipped MITOS2 output.")
    parser.add_argument("--circular", required=True, help="Treat genome as circular.")
    parser.add_argument("--noplots", required=True, help="Do not create plots.")
    parser.add_argument("--best", required=True, help="Use best model.")
    parser.add_argument("--ncbicode", required=True, help="Use NCBI start/stop codons.")

    # Returning parsed arguments.
    return parser.parse_args()


def main() -> int:
    """Run MITOS2 annotation.

    Returns:
        int: Exit code.
    """

    # Parsing arguments.
    args = parse_args()

    # Creating logger.
    logger = make_logger(
        name=f"mitos2.{args.sample_id}",
        log_file_path=args.log_file,
    )

    # Logging start.
    logger.info(f"Starting MITOS2 annotation for sample {args.sample_id}.")

    try:
        # Creating runner.
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
            best=parse_bool(args.best),
            ncbicode=parse_bool(args.ncbicode),
            logger=logger,
        )

        # Running MITOS2.
        result = runner.run()

        # Checking return code.
        if result.return_code != 0:
            logger.error(f"MITOS2 failed for sample {args.sample_id}.")
            logger.debug(f"MITOS2 return code: {result.return_code}")
            logger.debug(f"MITOS2 stdout:\n{result.stdout}")
            logger.debug(f"MITOS2 stderr:\n{result.stderr}")
            return result.return_code

        # Logging success.
        logger.info(f"MITOS2 annotation completed for sample {args.sample_id}.")
        return 0

    except Exception as error:
        # Logging failure.
        logger.exception(f"MITOS2 annotation failed for sample {args.sample_id}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())