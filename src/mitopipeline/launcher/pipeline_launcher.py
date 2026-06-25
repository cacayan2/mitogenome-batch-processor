"""pipeline_launcher.py

This module contains functionality for launching a mitopipeline run

The launcher is responsible for creating a PipelineJob, preparing runtime configuration, validating or generating the sample manifest, and invoking Snakemake with runtime-specific configuration.
"""

# Imports
import argparse
import shutil
import subprocess
from pathlib import Path
import yaml
import logging
import pandas as pd

from mitopipeline.models.pipeline_job import PipelineJob
from mitopipeline.manifest.sample_manifest import parse_sample_manifest
from mitopipeline.logging.logger_factory import make_logger

def normalize_manifest_paths(manifest_path: Path, output_manifest: Path) -> None:
    """Normalize manifest FASTQ paths and write a runtime manifest.
    
    Args:
        manifest_path (Path): The path to the manifest file.
        output_manifest (Path): The path to the output manifest file.

    Returns:
        None
    """
    # Reading manifest.
    df = pd.read_csv(manifest_path, sep = "\t")

    # Resolving paths relative to original manifest location.
    manifest_dir = manifest_path.parent

    for column in ["r1", "r2"]:
        df[column] = df[column].apply(
            lambda value: str(Path(value).resolve())
            if Path(str(value)).is_absolute()
            else str((manifest_dir / str(value)).resolve())
        )
    
    # Writing normalized runtime manifest.
    output_manifest.parent.mkdir(parents = True, exist_ok = True)
    df.to_csv(output_manifest, sep = "\t", index = False)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    # Creating argument parser. 
    parser = argparse.ArgumentParser(
        description = "Launches a mitopipeline run."
    )
    
    # Defining command line arguments.
    parser.add_argument("--config", required = True, help = "Path to the production configuration YAML file.")
    parser.add_argument("--snakefile", default = "ctrl/Snakefile", help = "Path to the Snakefile.")
    parser.add_argument("--cores", type = int, default = 1, help = "Number of cores to use.")
    parser.add_argument("--use-conda", action = "store_true", help = "Use conda environment.")
    parser.add_argument("--log-file", help = "Path to the logger.")

    # Returning parsed arguments.
    return parser.parse_args()

def load_config(config_path: Path) -> dict:
    """Load a YAML configuration file.
    
    Args:
        config_path (Path): The path to the YAML configuration file.
    
    Returns:
        dict: The loaded YAML configuration as a dictionary.
    """
    # Checking that the config file exists.
    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Loading config file.
    with config_path.open("r", encoding = "utf-8") as handle:
        config = yaml.safe_load(handle)

    # Checking loaded config.
    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
    
    # Returning config.
    return config

def discover_fastq_pairs(input_dir: Path, job: PipelineJob) -> list[dict[str, str]]:
    """Discover paired-end FASTQ files from an input directory.
    
    Args:
        input_dir (Path): The input directory.
    
    Returns:
        list[dict[str, str]]: A list of paired-end FASTQ file paths.
    """
    # Normalizing input directory.
    input_dir = Path(input_dir)

    # Checking input directory exists.
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Defining supported FASTQ suffixes.
    fastq_suffixes = [
        ".fastq.gz", 
        ".fq.gz",
        ".fastq",
        ".fq"
    ]

    # Collecting FASTQ files.
    fastq_files = []

    for suffix in fastq_suffixes:
        fastq_files.extend(input_dir.glob(f"*{suffix}"))

    # Sorting files for reproducible output.
    fastq_files = sorted(set(fastq_files))

    # Creating file lookup.
    r1_files = {}
    r2_files = {}

    # Classifying files as R1 or R2.
    for fastq in fastq_files:
        name = fastq.name

        if "_R1" in name:
            sample_id = name.split("_R1")[0]
            r1_files[sample_id] = fastq
        elif "_R2" in name:
            sample_id = name.split("_R2")[0]
            r2_files[sample_id] = fastq
        elif "_1" in name:
            sample_id = name.split("_1")[0]
            r1_files[sample_id] = fastq
        elif "_2" in name:
            sample_id = name.split("_2")[0]
            r2_files[sample_id] = fastq

    # Checking discovered pairs.
    sample_ids = sorted(set(r1_files.keys()) | set(r2_files.keys()))

    if len(sample_ids) == 0: 
        if job.job_logger is not None: job.job_logger.error(f"No FASTQ files found in {input_dir}.")
        raise FileNotFoundError(f"No FASTQ files found in {input_dir}.")
    
    # Building sample records.
    records = []

    for sample_id in sample_ids:
        if sample_id not in r1_files:
            raise ValueError(f"Missing R1 FASTQ for sample {sample_id}.")
        if sample_id not in r2_files:
            raise ValueError(f"Missing R2 FASTQ for sample {sample_id}.")
        
        records.append(
            {
                "sample_id": sample_id,
                "r1": str(r1_files[sample_id].resolve()),
                "r2": str(r2_files[sample_id].resolve()),
                "genus": "",
                "species": "",
                "source": "discovered_fastq",
            }
        )
    
    # Returning sample records. 
    return records

def write_sample_manifest(manifest_path: Path, records: list[dict[str, str]], job: PipelineJob) -> None:
    """Write sample records to a TSV manifest.
    
    Args: 
        manifest_path (Path): The path to the manifest file.
        records (list[dict[str, str]]): A list of sample records.
    
    Returns:
        None
    """
    # Creating parent directory.
    manifest_path.parent.mkdir(parents = True, exist_ok = True)

    # Defining manifest columns.
    columns = ["sample_id", "r1", "r2", "genus", "species", "source"]

    # Writing manifest.
    with manifest_path.open("w", encoding = "utf-8") as handle:
        handle.write("\t".join(columns) + "\n")

        for record in records: 
            row = [record.get(column, "") for column in columns]
            handle.write("\t".join(row) + "\n")

def prepare_runtime_manifest(config: dict, job: PipelineJob) -> Path:
    """Validate and prepare the runtime sample manifest.
    
    Args:
        config (dict): The configuration dictionary.
        job (PipelineJob): The job object.
        logger (logging.Logger): The logger object.
    
    Returns:
        Path: The prepared runtime sample manifest path.
    """ 

    # Creating runtime manifest path.
    runtime_manifest = job.job_dir / "validated_samples.tsv"

    # Getting manifest path from config.
    manifest_path = config.get("manifest")

    # If manifest is provided, validate and copy it into the job directory.
    if manifest_path is not None:
        manifest_path = Path(manifest_path)

        # Validating sample manifest by parsing it.
        parse_sample_manifest(manifest_path, logger = job.job_logger)

        # Copying manifest into job directory.
        normalize_manifest_paths(manifest_path, runtime_manifest)

        # Validating runtime manifest by parsing it. 
        parse_sample_manifest(runtime_manifest, logger = job.job_logger)

        # Logging manifest copy.
        job.job_logger.info(f"Copied validated manifest to {runtime_manifest}")

        # Returning runtime manifest path.
        return runtime_manifest
    
    # If no manifest is not provided, discover FASTQ files.
    input_dir = config.get("input_dir")

    if input_dir is None:
        if job.job_logger is not None: job.job_logger.error("Input directory not provided.")
        raise ValueError("Input directory not provided.")
    
    # Discovering FASTQ pairs.
    records = discover_fastq_pairs(Path(input_dir), job)

    # Writing discovered manifest.
    write_sample_manifest(runtime_manifest, records, job)

    # Validating generated manifest.
    parse_sample_manifest(runtime_manifest, logger = job.job_logger)

    # Logging discovered manifest.
    job.job_logger.info(f"Generated runtime manifest from discovered FASTQ files: {runtime_manifest}.")

    # Returning runtime manifest path.
    return runtime_manifest


def write_runtime_config(config: dict, job: PipelineJob, runtime_manifest: Path) -> Path:
    """Write a runtime configuration file for Snakemake.
    
    Args: 
        config (dict): The configuration dictionary.
        job (PipelineJob): The job object.
        runtime_manifest (Path): The runtime sample manifest path.
    
    Returns:
        Path: The path to the runtime configuration file.
    """
    # Copying config dictionary.
    runtime_config = dict(config)

    # Updating runtime-specific metadata.
    runtime_config["job_id"] = job.job_id
    runtime_config["manifest"] = str(runtime_manifest)
    runtime_config["output_root"] = str(job.parent_dir)

    # Creating runtime config.
    runtime_config_path = job.job_dir / "runtime_config.yaml"

    # Writing runtime config.
    with runtime_config_path.open("w", encoding = "utf-8") as handle:
        yaml.safe_dump(runtime_config, handle, sort_keys = False)

    # Logging runtime config.
    job.job_logger.info(f"Wrote runtime config to {runtime_config_path}.")

    # Returning runtime config path.
    return runtime_config_path

def run_snakemake(
        snakefile: Path, 
        runtime_config: Path, 
        cores: int, 
        use_conda: bool, 
        logger: logging.Logger
    ) -> subprocess.CompletedProcess:
    """Run Snakemake using the runtime configuration.
    
    Args:
        snakefile_path (Path): The path to the Snakefile.
        runtime_config_path (Path): The path to the runtime configuration file.
        cores (int): The number of cores to use.
        use_conda (bool): Whether to use conda environment.
        logger (logging.Logger): The logger object.

    Returns:
        subprocess.CompletedProcess: The result of the Snakemake run.
    """
    # Building Snakemake command.
    command = [
        "snakemake",
        "-s",
        str(snakefile),
        "--configfile",
        str(runtime_config),
        "--cores",
        str(cores),
    ]

    # Adding conda flag if requested.
    if use_conda:
        command.append("--use-conda")

    # Logging command.
    logger.info(f"Starting snakemake execution.")
    logger.debug(f"Snakemake command: {command}")

    # Running command.
    result = subprocess.run(command, capture_output = True, text = True)

    # Logging output.
    logger.debug(f"Snakemake stdout: {result.stdout}")
    logger.debug(f"Snakemake stderr: {result.stderr}")

    # Logging status.
    if result.returncode == 0:
        logger.info(f"Snakemake execution completed successfully.")
    else:
        logger.error(f"Snakemake execution failed with return code {result.returncode}.")
    
    # Returning result.
    return result

def launch_pipeline(
        config_path: Path,
        snakefile: Path,
        cores: int = 1,
        use_conda: bool = False,
    ) -> int:
    """Launch a mitopipeline workflow run.

    Args:
        config_path (Path): The path to the configuration file.
        snakefile (Path): The path to the Snakefile.
        cores (int, optional): The number of cores to use. Defaults to 1.
        use_conda (bool, optional): Whether to use conda environment. Defaults to False.

    Returns:
        int: Snakemake return code.
    """

    # Loading production configuration.
    config = load_config(config_path)

    # Creating pipeline job.
    output_root = Path(config["output_root"])
    job = PipelineJob(parent_dir = output_root)

    try:
        # Preparing runtime sample manifest.
        runtime_manifest = prepare_runtime_manifest(config, job)

        # Writing runtime config.
        runtime_config = write_runtime_config(config, job, runtime_manifest)

        # Running Snakemake.
        result = run_snakemake(
            snakefile = snakefile, 
            runtime_config = runtime_config, 
            cores = cores, 
            use_conda = use_conda, 
            logger = job.job_logger,
            )

        # Marking job status.
        if result.returncode == 0:
            job.mark_completed()
        else: 
            job.mark_failed()

    except Exception as error:
        # Marking failed job.
        job.job_logger.exception(f"Pipeline launch failed: {error}")
        job.mark_failed()
        return 1
    
    # Returning Snakemake return code.
    return result.returncode
    
def main() -> int:
    """Run the pipeline launcher from the command line.
    
    Returns: 
        int: Exit code.
    """
    # Parsing arguments. 
    args = parse_args()

    # Launching pipeline.
    return launch_pipeline(
        config_path = Path(args.config),
        snakefile = Path(args.snakefile),
        cores = args.cores,
        use_conda = args.use_conda,
    )

if __name__ == "__main__":
    raise SystemExit(main())