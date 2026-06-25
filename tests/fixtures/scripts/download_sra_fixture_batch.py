"""download_sra_fixture_batch.py

This script prepares real paired-end SRA fixture datasets, compresses the
resulting FASTQ files, and writes a manifest that can be used by the
mitopipeline workflow.

If cached SRA files already exist, the script reuses them and does not download
new data. The generated FASTQ files should not be committed to GitHub.
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
    """This function returns a configured logger object."""

    log_file = Path(log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    file_formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(message)s | %(filename)s:%(lineno)d"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Batch prepare SRA fixture data and create a mitopipeline manifest."
    )

    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output-fastq-dir", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--sra-cache-dir", required=True)
    parser.add_argument("--log-file", default="tests/fixtures/logs/download_sra_fixture_batch.log")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")

    return parser.parse_args()


def require_command(command: str) -> None:
    """Verify that an external command exists."""

    if shutil.which(command) is None:
        raise RuntimeError(
            f"Required command not found: {command}. "
            "Install dependencies with: conda install -c conda-forge -c bioconda sra-tools"
        )


def run_command(command: list[str], logger: logging.Logger) -> None:
    """Run a shell command and raise an error if it fails."""

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
    """Read the SRA source manifest."""

    with source_manifest.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)

    if len(rows) == 0:
        raise ValueError(f"Source manifest is empty: {source_manifest}")

    required_columns = {"sample_id", "sra_run", "genus", "species", "source"}
    missing_columns = required_columns - set(rows[0].keys())

    if len(missing_columns) > 0:
        raise ValueError(f"Source manifest is missing required columns: {missing_columns}")

    return rows


def find_cached_sra(sra_cache_dir: Path, sra_run: str) -> Path | None:
    """Find an existing cached SRA file.

    Args:
        sra_cache_dir (Path): SRA cache directory.
        sra_run (str): SRA run accession.

    Returns:
        Path | None: Cached SRA file if present.
    """

    expected_path = sra_cache_dir / sra_run / f"{sra_run}.sra"

    if expected_path.exists():
        return expected_path

    return None


def gzip_file(input_path: Path, output_path: Path) -> None:
    """Compress a file using gzip."""

    with input_path.open("rb") as source:
        with gzip.open(output_path, "wb") as target:
            shutil.copyfileobj(source, target)


def count_fastq_records_gz(fastq_gz_path: Path) -> int:
    """Count records in a gzipped FASTQ file."""

    line_count = 0

    with gzip.open(fastq_gz_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_count, _ in enumerate(handle, start=1):
            pass

    if line_count % 4 != 0:
        raise ValueError(f"FASTQ line count is not divisible by 4: {fastq_gz_path}")

    return line_count // 4


def prepare_one_sample(row: dict[str, str],
                       output_fastq_dir: Path,
                       sra_cache_dir: Path,
                       threads: int,
                       overwrite: bool,
                       logger: logging.Logger) -> dict[str, str]:
    """Prepare one SRA sample without subsampling."""

    sample_id = row["sample_id"].strip()
    sra_run = row["sra_run"].strip()
    genus = row.get("genus", "").strip()
    species = row.get("species", "").strip()
    source = row.get("source", "").strip()

    final_r1 = output_fastq_dir / f"{sample_id}_R1.fastq.gz"
    final_r2 = output_fastq_dir / f"{sample_id}_R2.fastq.gz"

    raw_r1 = output_fastq_dir / f"{sra_run}_1.fastq"
    raw_r2 = output_fastq_dir / f"{sra_run}_2.fastq"

    if not overwrite and (final_r1.exists() or final_r2.exists()):
        raise FileExistsError(f"FASTQ outputs already exist for {sample_id}. Use --overwrite.")

    cached_sra = find_cached_sra(sra_cache_dir, sra_run)

    if cached_sra is None:
        logger.info(f"Cached SRA not found for {sample_id}; downloading {sra_run}.")
        run_command(["prefetch", sra_run, "-O", str(sra_cache_dir)], logger)
        cached_sra = find_cached_sra(sra_cache_dir, sra_run)

    if cached_sra is None:
        raise FileNotFoundError(f"Cached SRA file could not be found after prefetch: {sra_run}")

    logger.info(f"Converting cached SRA for {sample_id}: {cached_sra}")

    run_command(
        [
            "fasterq-dump",
            str(cached_sra),
            "--split-files",
            "--threads",
            str(threads),
            "-O",
            str(output_fastq_dir),
        ],
        logger,
    )

    if not raw_r1.exists() or not raw_r2.exists():
        raise FileNotFoundError(
            f"Expected paired FASTQ files were not created for {sra_run}: {raw_r1}, {raw_r2}"
        )

    logger.info(f"Compressing all reads for {sample_id}.")
    gzip_file(raw_r1, final_r1)
    gzip_file(raw_r2, final_r2)

    raw_r1.unlink(missing_ok=True)
    raw_r2.unlink(missing_ok=True)

    r1_count = count_fastq_records_gz(final_r1)
    r2_count = count_fastq_records_gz(final_r2)

    if r1_count != r2_count:
        raise ValueError(f"Read counts do not match for {sample_id}: R1={r1_count}, R2={r2_count}")

    logger.info(f"Finished {sample_id}: {r1_count} read pairs.")

    return {
        "sample_id": sample_id,
        "r1": str(final_r1),
        "r2": str(final_r2),
        "genus": genus,
        "species": species,
        "source": source,
    }


def write_pipeline_manifest(output_manifest: Path, rows: list[dict[str, str]]) -> None:
    """Write a mitopipeline-compatible sample manifest."""

    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    with output_manifest.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["sample_id", "r1", "r2", "genus", "species", "source"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """Run the batch SRA fixture preparation script."""

    args = parse_args()

    source_manifest = Path(args.source_manifest)
    output_fastq_dir = Path(args.output_fastq_dir)
    output_manifest = Path(args.output_manifest)
    sra_cache_dir = Path(args.sra_cache_dir)

    output_fastq_dir.mkdir(parents=True, exist_ok=True)
    sra_cache_dir.mkdir(parents=True, exist_ok=True)

    logger = make_logger("download_sra_fixture_batch", args.log_file)

    require_command("prefetch")
    require_command("fasterq-dump")

    source_rows = read_source_manifest(source_manifest)

    output_rows = []

    for row in source_rows:
        output_row = prepare_one_sample(
            row=row,
            output_fastq_dir=output_fastq_dir,
            sra_cache_dir=sra_cache_dir,
            threads=args.threads,
            overwrite=args.overwrite,
            logger=logger,
        )

        output_rows.append(output_row)

    write_pipeline_manifest(output_manifest, output_rows)

    logger.info(f"Wrote mitopipeline manifest: {output_manifest}")
    logger.info("SRA fixture preparation completed successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())