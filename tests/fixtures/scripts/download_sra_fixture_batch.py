"""download_sra_fixture_batch.py

This script downloads real paired-end SRA datasets, subsamples them, compresses
the resulting FASTQ files, and writes a manifest that can be used by the
mitopipeline workflow.

The input manifest should contain SRA run accessions and sample metadata.
The downloaded FASTQ files should not be committed to GitHub.

Example:
    python scripts/download_sra_fixture_batch.py \
        --source-manifest tests/fixtures/manifests/sra_fixture_sources.tsv \
        --output-fastq-dir tests/fixtures/fastq_real \
        --output-manifest tests/fixtures/manifests/valid_real_sra.tsv \
        --sra-cache-dir tests/fixtures/sra_cache \
        --max-read-pairs 50000 \
        --overwrite
"""

# Imports
import argparse
import csv
import gzip
import logging
import shutil
import subprocess
from pathlib import Path


def make_logger(name: str,
                log_file_path: str | Path,
                console_level: int = logging.INFO,
                file_level: int = logging.DEBUG) -> logging.Logger:
    """This function returns a configured logger object.

    Args:
        name (str): The name of the logger.
        log_file_path (str | Path): The path to the log file.
        console_level (int, optional): The level of the console handler. Defaults to logging.INFO.
        file_level (int, optional): The level of the file handler. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: A configured logger object.
    """

    # Setting the log_file, creating a parent directory if necessary.
    log_file = Path(log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Creating the logger object and setting the level.
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if make_logger() is called multiple times.
    if logger.handlers:
        return logger

    # Defining formatter for console and file logs.
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    file_formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(message)s | %(filename)s:%(lineno)d"
    )

    # Creating console handler.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Creating file handler.
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # Assigning handlers.
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Returning logger.
    return logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    # Creating argument parser.
    parser = argparse.ArgumentParser(
        description="Batch download SRA fixture data and create a mitopipeline manifest."
    )

    # Defining input and output arguments.
    parser.add_argument("--source-manifest", required=True, help="TSV containing SRA runs and metadata.")
    parser.add_argument("--output-fastq-dir", required=True, help="Directory for generated FASTQ files.")
    parser.add_argument("--output-manifest", required=True, help="Output mitopipeline sample manifest.")
    parser.add_argument("--sra-cache-dir", required=True, help="Directory for SRA cache files.")
    parser.add_argument("--log-file", default="tests/fixtures/logs/download_sra_fixture_batch.log")

    # Defining processing arguments.
    parser.add_argument("--max-read-pairs", type=int, default=50000)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")

    # Returning parsed arguments.
    return parser.parse_args()


def require_command(command: str) -> None:
    """Verify that an external command exists.

    Args:
        command (str): The command to check.

    Returns:
        None
    """

    if shutil.which(command) is None:
        raise RuntimeError(
            f"Required command not found: {command}. "
            "Install dependencies with: conda install -c conda-forge -c bioconda sra-tools"
        )


def run_command(command: list[str], logger: logging.Logger) -> None:
    """Run a shell command and raise an error if it fails.

    Args:
        command (list[str]): The command to run.
        logger (logging.Logger): Logger object.

    Returns:
        None
    """

    logger.debug(f"Running command: {command}")

    result = subprocess.run(command, capture_output=True, text=True)

    logger.debug(f"stdout: {result.stdout}")
    logger.debug(f"stderr: {result.stderr}")

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            f"{' '.join(command)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


def read_source_manifest(source_manifest: Path) -> list[dict[str, str]]:
    """Read the SRA source manifest.

    Args:
        source_manifest (Path): Path to the SRA source manifest.

    Returns:
        list[dict[str, str]]: List of source manifest rows.
    """

    # Reading source manifest.
    with source_manifest.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    # Checking manifest is not empty.
    if len(rows) == 0:
        raise ValueError(f"Source manifest is empty: {source_manifest}")

    # Checking required columns.
    required_columns = {"sample_id", "sra_run", "genus", "species", "source"}
    missing_columns = required_columns - set(rows[0].keys())

    if len(missing_columns) > 0:
        raise ValueError(f"Source manifest is missing required columns: {missing_columns}")

    # Returning rows.
    return rows


def subsample_fastq(input_path: Path, output_path: Path, max_records: int) -> None:
    """Subsample the first N FASTQ records from an input FASTQ file.

    Args:
        input_path (Path): Input FASTQ path.
        output_path (Path): Output FASTQ path.
        max_records (int): Maximum number of records to write.

    Returns:
        None
    """

    # Writing the first max_records FASTQ records.
    records_written = 0

    with input_path.open("rt", encoding="utf-8", errors="replace") as source:
        with output_path.open("wt", encoding="utf-8") as target:
            while records_written < max_records:
                record = [source.readline() for _ in range(4)]

                if not record[0]:
                    break

                if any(line == "" for line in record):
                    raise ValueError(f"Incomplete FASTQ record found in {input_path}")

                target.writelines(record)
                records_written += 1


def gzip_file(input_path: Path, output_path: Path) -> None:
    """Compress a file using gzip.

    Args:
        input_path (Path): Input file.
        output_path (Path): Output gzip file.

    Returns:
        None
    """

    with input_path.open("rb") as source:
        with gzip.open(output_path, "wb") as target:
            shutil.copyfileobj(source, target)


def count_fastq_records_gz(fastq_gz_path: Path) -> int:
    """Count records in a gzipped FASTQ file.

    Args:
        fastq_gz_path (Path): Path to gzipped FASTQ.

    Returns:
        int: Number of FASTQ records.
    """

    # Counting lines.
    line_count = 0

    with gzip.open(fastq_gz_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_count, _ in enumerate(handle, start=1):
            pass

    # Validating line count.
    if line_count % 4 != 0:
        raise ValueError(f"FASTQ line count is not divisible by 4: {fastq_gz_path}")

    # Returning record count.
    return line_count // 4


def download_one_sample(row: dict[str, str],
                        output_fastq_dir: Path,
                        sra_cache_dir: Path,
                        max_read_pairs: int,
                        threads: int,
                        overwrite: bool,
                        logger: logging.Logger) -> dict[str, str]:
    """Download and process one SRA sample.

    Args:
        row (dict[str, str]): Source manifest row.
        output_fastq_dir (Path): Output FASTQ directory.
        sra_cache_dir (Path): SRA cache directory.
        max_read_pairs (int): Maximum read pairs to keep.
        threads (int): Number of threads for fasterq-dump.
        overwrite (bool): Whether to overwrite existing files.
        logger (logging.Logger): Logger object.

    Returns:
        dict[str, str]: Row for mitopipeline sample manifest.
    """

    # Extracting metadata.
    sample_id = row["sample_id"].strip()
    sra_run = row["sra_run"].strip()
    genus = row.get("genus", "").strip()
    species = row.get("species", "").strip()
    source = row.get("source", "").strip()

    # Creating output paths.
    final_r1 = output_fastq_dir / f"{sample_id}_R1.fastq.gz"
    final_r2 = output_fastq_dir / f"{sample_id}_R2.fastq.gz"

    raw_r1 = output_fastq_dir / f"{sra_run}_1.fastq"
    raw_r2 = output_fastq_dir / f"{sra_run}_2.fastq"

    sub_r1 = output_fastq_dir / f"{sample_id}_R1.fastq"
    sub_r2 = output_fastq_dir / f"{sample_id}_R2.fastq"

    # Avoiding accidental overwrite.
    if not overwrite and (final_r1.exists() or final_r2.exists()):
        raise FileExistsError(f"FASTQ outputs already exist for {sample_id}. Use --overwrite.")

    # Logging sample.
    logger.info(f"Downloading sample {sample_id} from {sra_run}.")

    # Downloading SRA file.
    run_command(["prefetch", sra_run, "-O", str(sra_cache_dir)], logger)

    # Converting SRA to FASTQ.
    run_command(
        [
            "fasterq-dump",
            str(sra_cache_dir / sra_run),
            "--split-files",
            "--threads",
            str(threads),
            "-O",
            str(output_fastq_dir),
        ],
        logger,
    )

    # Checking paired-end files.
    if not raw_r1.exists() or not raw_r2.exists():
        raise FileNotFoundError(
            f"Expected paired FASTQ files were not created for {sra_run}: {raw_r1}, {raw_r2}"
        )

    # Subsampling reads.
    if max_read_pairs > 0:
        logger.info(f"Subsampling {sample_id} to {max_read_pairs} read pairs.")
        subsample_fastq(raw_r1, sub_r1, max_read_pairs)
        subsample_fastq(raw_r2, sub_r2, max_read_pairs)
    else:
        logger.info(f"Keeping all read pairs for {sample_id}.")
        shutil.move(raw_r1, sub_r1)
        shutil.move(raw_r2, sub_r2)

    # Compressing outputs.
    logger.info(f"Compressing FASTQ files for {sample_id}.")
    gzip_file(sub_r1, final_r1)
    gzip_file(sub_r2, final_r2)

    # Removing intermediate files.
    raw_r1.unlink(missing_ok=True)
    raw_r2.unlink(missing_ok=True)
    sub_r1.unlink(missing_ok=True)
    sub_r2.unlink(missing_ok=True)

    # Counting reads.
    r1_count = count_fastq_records_gz(final_r1)
    r2_count = count_fastq_records_gz(final_r2)

    if r1_count != r2_count:
        raise ValueError(f"Read counts do not match for {sample_id}: R1={r1_count}, R2={r2_count}")

    logger.info(f"Finished {sample_id}: {r1_count} read pairs.")

    # Returning manifest row.
    return {
        "sample_id": sample_id,
        "r1": str(final_r1),
        "r2": str(final_r2),
        "genus": genus,
        "species": species,
        "source": source,
    }


def write_pipeline_manifest(output_manifest: Path, rows: list[dict[str, str]]) -> None:
    """Write a mitopipeline-compatible sample manifest.

    Args:
        output_manifest (Path): Output manifest path.
        rows (list[dict[str, str]]): Manifest rows.

    Returns:
        None
    """

    # Creating parent directory.
    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    # Writing manifest.
    with output_manifest.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["sample_id", "r1", "r2", "genus", "species", "source"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """Run the batch SRA fixture downloader.

    Returns:
        int: 0 if successful.
    """

    # Parsing arguments.
    args = parse_args()

    # Creating paths.
    source_manifest = Path(args.source_manifest)
    output_fastq_dir = Path(args.output_fastq_dir)
    output_manifest = Path(args.output_manifest)
    sra_cache_dir = Path(args.sra_cache_dir)

    # Creating directories.
    output_fastq_dir.mkdir(parents=True, exist_ok=True)
    sra_cache_dir.mkdir(parents=True, exist_ok=True)

    # Creating logger.
    logger = make_logger("download_sra_fixture_batch", args.log_file)

    # Checking external dependencies.
    require_command("prefetch")
    require_command("fasterq-dump")

    # Reading source manifest.
    source_rows = read_source_manifest(source_manifest)

    # Processing samples.
    output_rows = []

    for row in source_rows:
        output_row = download_one_sample(
            row=row,
            output_fastq_dir=output_fastq_dir,
            sra_cache_dir=sra_cache_dir,
            max_read_pairs=args.max_read_pairs,
            threads=args.threads,
            overwrite=args.overwrite,
            logger=logger,
        )

        output_rows.append(output_row)

    # Writing mitopipeline manifest.
    write_pipeline_manifest(output_manifest, output_rows)

    logger.info(f"Wrote mitopipeline manifest: {output_manifest}")
    logger.info("SRA fixture batch download completed successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())