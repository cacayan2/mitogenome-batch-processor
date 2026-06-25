"""run_getorganelle.py

Execution layer connecting GetOrganelle to Snakemake.
"""

# Imports
import argparse
from logging import Logger
from pathlib import Path
from mitopipeline.api.getorganelle import GetOrganelleRunner
from mitopipeline.models.sample import Sample
from mitopipeline.logging.logger_factory import make_logger

def parse_args() -> argparse.Namespace:
    """
    Pass command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    # Define arguments for files.
    parser = argparse.ArgumentParser(
        description="Run GetOrganelle on a single sequencing sample."
    )
    parser.add_argument(
        "--sample-id",
        required=True,
        help="Unique identifier for the sample."
    )
    parser.add_argument(
        "--in1",
        required=True,
        help="Path to the trimmed R1 FASTQ."
    )
    parser.add_argument(
        "--in2",
        required=True,
        help="Path to the trimmed R2 FASTQ."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where GetOrganelle outputs will be written."
    )
    parser.add_argument(
        "--working-dir",
        required=True,
        help="Working directory for GetOrganelle."
    )
    parser.add_argument(
        "--organelle-type",
        required=True,
        help="GetOrganelle database type (e.g. animal_mt)."
    )
    parser.add_argument(
        "--threads",
        type=int,
        required=True,
        help="Number of CPU threads."
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the log file."
    )

    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--kmer", default=None)
    parser.add_argument("--word-size", type=int, default=None)
    parser.add_argument("--pre-grouping", type=float, default=None)
    parser.add_argument("--max-reads", type=int, default=None)
    parser.add_argument("--target-coverage", type=int, default=None)
    parser.add_argument("--min-read-length", type=int, default=None)
    parser.add_argument("--max-read-length", type=int, default=None)
    parser.add_argument("--expected-max-size", type=int, default=None)
    parser.add_argument("--expected-min-size", type=int, default=None)
    parser.add_argument("--seed-file", default=None)
    parser.add_argument("--genes-file", default=None)
    parser.add_argument("--exclude-fasta", default=None)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--round-output-prefix", default=None)
    parser.add_argument("--blast-path", default=None)
    parser.add_argument("--bandage-path", default=None)
    parser.add_argument("--spades-path", default=None)

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing output directory."
    )
    parser.add_argument(
        "--continue-run",
        action="store_true",
        help="Continue a previous GetOrganelle run."
    )
    parser.add_argument(
        "--fast-mode",
        action="store_true",
        help="Enable fast mode."
    )
    parser.add_argument(
        "--disentangle",
        action="store_true",
        help="Enable graph disentangling."
    )
    parser.add_argument(
        "--reverse-lsc",
        action="store_true",
        help="Reverse the LSC orientation."
    )
    parser.add_argument(
        "--no-slim",
        action="store_true",
        help="Disable graph slimming."
    )
    parser.add_argument(
        "--keep-temp-files",
        action="store_true",
        help="Keep temporary files."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose GetOrganelle output."
    )

    return parser.parse_args()

def build_sample(args) -> Sample:
    """
    Construct a Sample object from CLI arguments.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Sample: A Sample object.
    """
    return Sample(sample_id = args.sample_id, r1 = Path(args.in1), r2 = Path(args.in2))

def build_logger(args) -> Logger:
    """
    Construct a logger object using the make_logger function from the logger module.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Logger: A logger object.
    """
    return make_logger(name = "getorganelle", log_file_path = args.log_file)

def main() -> int:
    """
    Run GetOrganelle for a single sequencing sample.

    Returns:
        int: 0 if successful, 1 otherwise.
    """
    # Setting none object for logger.
    logger = None

    try:
        # Obtaining the parsed arguments.
        args = parse_args()

        # Building the logger.
        logger = build_logger(args)

        # Constructing the sample object.
        sample = build_sample(args)

        # Logging the sample object. 
        if logger is not None: logger.info(f"Starting GetOrganelle execution for sample {sample.sample_id}.")

        # Creating tool options dictionary.
        tool_options = {
            "max_rounds": args.max_rounds,
            "kmer": args.kmer,
            "word_size": args.word_size,
            "pre_grouping": args.pre_grouping,
            "max_reads": args.max_reads,
            "target_coverage": args.target_coverage,
            "min_read_length": args.min_read_length,
            "max_read_length": args.max_read_length,
            "expected_max_size": args.expected_max_size,
            "expected_min_size": args.expected_min_size,
            "seed_file": args.seed_file,
            "genes_file": args.genes_file,
            "exclude_fasta": args.exclude_fasta,
            "prefix": args.prefix,
            "round_output_prefix": args.round_output_prefix,
            "blast_path": args.blast_path,
            "bandage_path": args.bandage_path,
            "spades_path": args.spades_path,
            "overwrite": args.overwrite,
            "continue_run": args.continue_run,
            "fast_mode": args.fast_mode,
            "disentangle": args.disentangle,
            "reverse_lsc": args.reverse_lsc,
            "no_slim": args.no_slim,
            "keep_temp_files": args.keep_temp_files,
            "verbose": args.verbose,
        }

        # Creating the GetOrganelle API Object.
        runner = GetOrganelleRunner(
            working_dir = Path(args.working_dir),
            output_dir = Path(args.output_dir),
            sample = sample,
            organelle_type = args.organelle_type,
            tool_options = tool_options,
            threads = args.threads,
            logger = logger,
        )

        # Running GetOrganelle and obtaining CommandResult.
        result = runner.run()

        # Checking execution result.
        if not result.success:
            if logger:
                logger.error(f"GetOrganelle execution failed for sample {sample.sample_id}.")
                logger.debug(f"GetOrganelle return code: {result.return_code}")
                logger.debug(f"GetOrganelle stderr: {result.stderr}")
                logger.debug(f"GetOrganelle stdout: {result.stdout}")
            return result.return_code if result.return_code != 0 else 1
        if logger:
            logger.info(f"GetOrganelle execution successful for sample {sample.sample_id}.")
            logger.debug(f"GetOrganelle runtime seconds: {result.runtime_seconds}")
        return 0
    except Exception as error:
        if logger:
            logger.exception(f"GetOrganelle execution failed: {error}.")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())