"""
run_fastqc_raw.py

Execution layer for FastQC on raw sequencing data.
"""

# Imports
import argparse
from pathlib import pathlib
from mitopipeline.api.fastqc import FastQCRunner
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.models.sample import Sample

def parse_args() -> argparse.Namespace
    """
    Parses the command line arguments for this script.

    Returns:
        argparse.Namespace: The parsed command line arguments.
    """
    # Creating the argument parser.
    parser = argparse.ArgumentParser(description = "Runs FastQC on raw sequencing data.")

    # Adding arguments to the parser.
    parser.add_argument("--sample-id", type = str, required = True, help = "The sample id.")
    parser.add_argument("--r1", type = str, required = True, help = "The path to the R2 fastq file.")
    parser.add_argument("--r2", type = str, required = True, help = "The path to the R2 fastq file.")
    parser.add_argument("--output-dir", type = str, required = True, help = "The path to the output directory.")
    parser.add_argument("--working-dir", type = str, required = True, help = "The path to the working directory.")
    parser.add_argument("--log-file", type = str, required = True, help = "The path to the log file.")
    parser.add_argument("--threads", type = int, required = True, help = "The number of threads to use.")

    # Parsing the arguments.
    return parser.parse_args()

def main() -> int:
    """
    Runs the FastQC on raw sequencing data.

    Returns:
        int: The return code for the process.
    """
    # Parsing the command line arguments.
    args = parse_args()

    # Creating the logger.
    logger = make_logger(
        name = "fastqc_raw",
        log_file_path = component_log_file,