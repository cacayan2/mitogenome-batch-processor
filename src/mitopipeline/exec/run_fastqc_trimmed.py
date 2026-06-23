"""run_fastqc_trimmed.py

Execution layer connecting FastQC to Snakemake - this is for data that is already trimmed.
"""

# Imports
import argparse
from logging import Logger
from pathlib import Path
from mitopipeline.api.fastqc import FastQCRunner
from mitopipeline.models.sample import Sample
from mitopipeline.logging.logger_factory import make_logger

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description = "Process sample inputs and directory paths."
    )

    # Define arguments for files.
    parser.add_argument("--sample-id", help = "The unique identifier for the sample.")
    parser.add_argument("--r1", help = "Path to the R1 input file.")
    parser.add_argument("--r2", help = "Path to the R2 input file.")
    parser.add_argument("--output-dir", help = "Path to the output directory.")
    parser.add_argument("--working-dir", help = "Path to the working directory.")
    parser.add_argument("--log-file", help = "Path to the logger.")

    # Return the parsed arguments.
    return parser.parse_args()

def build_sample(args) -> Sample:
    """Construct a Sample object from CLI arguments.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        Sample: A Sample object.
    """
    return Sample(sample_id = args.sample_id, r1 = Path(args.r1), r2 = Path(args.r2))

def build_logger(args) -> Logger:
    """Constructs a logger object using the make_logger function from the logger module.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        Logger: A logger object.
    """
    return make_logger(name = "fastqc.trimmed", log_file_path = args.log_file)

def main() -> int:
    """Run FastQC for a single sequencing sample.
    
    Returns:
        int: 0 if successful, 1 otherwise.
    """
    try:
        # Obtaining the parsed arguments.
        args = parse_args()

        # Building the logger. 
        logger = build_logger(args)

        # Constructing the sample object.
        sample = build_sample(args)

        # Logging the sample object.
        if logger is not None: logger.info(f"Starting FastQC execution for trimmed sample {sample.sample_id}.")

        # Creating the FastQC API object.
        runner = FastQCRunner(sample = sample, output_dir = Path(args.output_dir), working_dir = Path(args.working_dir), logger = logger)

        # Running FastQC and obtaining CommandResult.
        result = runner.run()

        # Checking execution result.
        if not result.success:
            if logger: 
                logger.error(f"FastQC failed for trimmed sample {sample.sample_id}.")
                logger.debug(f"FastQC return code: {result.return_code}")
                logger.debug(f"FastQC stdout:\n{result.stdout}")
                logger.debug(f"FastQC stderr:\n{result.stderr}")
            
            return result.return_code if result.return_code != 0 else 1
        if logger:
            logger.info(f"FastQC completed successfully for trimmed sample {sample.sample_id}.")
            logger.debug(f"FastQC runtime seconds: {result.runtime_seconds}")
        return 0
    except Exception as error:
        if logger:
            logger.exception(f"FastQC execution failed: {error}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())