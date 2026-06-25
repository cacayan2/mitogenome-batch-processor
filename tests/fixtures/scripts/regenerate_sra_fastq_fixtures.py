"""regenerate_sra_fastq_fixtures.py

Regenerate real FASTQ fixture files from already-downloaded SRA cache files.

This script does not download new SRA data. It expects `.sra` files to already
exist in the local SRA cache directory. It converts each cached SRA run to
paired FASTQ files, optionally limits the number of read pairs, compresses the
FASTQ files, and writes a portable manifest for downstream pipeline testing.
"""

# Imports
import argparse
import gzip
import shutil
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Regenerate paired FASTQ fixtures from cached SRA files."
    )

    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to source manifest containing sample_id and sra_run columns.",
    )
    parser.add_argument(
        "--sra-cache-dir",
        default="tests/fixtures/sra_cache",
        help="Directory containing cached SRA run folders.",
    )
    parser.add_argument(
        "--output-dir",
        default="tests/fixtures/fastq_real",
        help="Directory where regenerated FASTQ fixtures will be written.",
    )
    parser.add_argument(
        "--output-manifest",
        default="tests/fixtures/manifests/valid_real_sra.tsv",
        help="Path to write the regenerated portable manifest.",
    )
    parser.add_argument(
        "--max-read-pairs",
        type=int,
        default=500000,
        help="Maximum paired reads to keep per sample.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of threads for fasterq-dump.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing regenerated FASTQ files.",
    )

    return parser.parse_args()


def read_manifest(manifest_path: Path) -> list[dict[str, str]]:
    """Read a tab-delimited SRA fixture manifest.

    Args:
        manifest_path (Path): Path to the source manifest.

    Returns:
        list[dict[str, str]]: Manifest rows.
    """

    rows = []

    with manifest_path.open("r", encoding="utf-8") as handle:
        header = handle.readline().strip().split("\t")

        for line in handle:
            if not line.strip():
                continue

            values = line.rstrip("\n").split("\t")
            rows.append(dict(zip(header, values)))

    return rows


def run_command(command: list[str]) -> None:
    """Run a shell command and raise if it fails.

    Args:
        command (list[str]): Command to run.

    Returns:
        None
    """

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            f"{' '.join(command)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


def find_sra_file(sra_cache_dir: Path, sra_run: str) -> Path:
    """Find a cached SRA file for a run.

    Args:
        sra_cache_dir (Path): Local SRA cache directory.
        sra_run (str): SRA run accession.

    Returns:
        Path: Path to cached SRA file.
    """

    sra_file = sra_cache_dir / sra_run / f"{sra_run}.sra"

    if not sra_file.exists():
        raise FileNotFoundError(f"Cached SRA file not found: {sra_file}")

    return sra_file


def count_fastq_records(fastq_path: Path) -> int:
    """Count FASTQ records in an uncompressed FASTQ file.

    Args:
        fastq_path (Path): Path to FASTQ file.

    Returns:
        int: Number of FASTQ records.
    """

    line_count = 0

    with fastq_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_count, _ in enumerate(handle, start=1):
            pass

    return line_count // 4


def write_limited_fastq(input_path: Path, output_path: Path, max_records: int) -> None:
    """Write a limited number of FASTQ records to a gzip-compressed FASTQ.

    Args:
        input_path (Path): Uncompressed input FASTQ path.
        output_path (Path): Gzip-compressed output FASTQ path.
        max_records (int): Maximum records to write.

    Returns:
        None
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    max_lines = max_records * 4

    with input_path.open("rb") as input_handle:
        with gzip.open(output_path, "wb") as output_handle:
            for line_number, line in enumerate(input_handle, start=1):
                if line_number > max_lines:
                    break

                output_handle.write(line)


def regenerate_sample(
    row: dict[str, str],
    sra_cache_dir: Path,
    output_dir: Path,
    max_read_pairs: int,
    threads: int,
    overwrite: bool,
) -> dict[str, str]:
    """Regenerate paired FASTQ fixtures for one SRA sample.

    Args:
        row (dict[str, str]): Manifest row.
        sra_cache_dir (Path): Local SRA cache directory.
        output_dir (Path): FASTQ fixture output directory.
        max_read_pairs (int): Maximum read pairs to keep.
        threads (int): Number of fasterq-dump threads.
        overwrite (bool): Whether to overwrite existing outputs.

    Returns:
        dict[str, str]: Runtime manifest row.
    """

    sample_id = row["sample_id"]
    sra_run = row["sra_run"]

    output_r1 = output_dir / f"{sample_id}_R1.fastq.gz"
    output_r2 = output_dir / f"{sample_id}_R2.fastq.gz"

    if output_r1.exists() and output_r2.exists() and not overwrite:
        print(f"Skipping {sample_id}; outputs already exist.")
        return {
            "sample_id": sample_id,
            "r1": output_r1.name,
            "r2": output_r2.name,
            "genus": row.get("genus", ""),
            "species": row.get("species", ""),
            "source": row.get("source", "NCBI_SRA"),
        }

    sra_file = find_sra_file(sra_cache_dir, sra_run)

    temp_dir = output_dir / f"{sample_id}_tmp"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"Converting {sample_id} from cached SRA: {sra_file}")

    run_command(
        [
            "fasterq-dump",
            str(sra_file),
            "--split-files",
            "--threads",
            str(threads),
            "--outdir",
            str(temp_dir),
        ]
    )

    temp_r1 = temp_dir / f"{sra_run}_1.fastq"
    temp_r2 = temp_dir / f"{sra_run}_2.fastq"

    if not temp_r1.exists() or not temp_r2.exists():
        raise FileNotFoundError(
            f"Expected paired FASTQ files were not produced for {sample_id}."
        )

    available_pairs = min(
        count_fastq_records(temp_r1),
        count_fastq_records(temp_r2),
    )

    pairs_to_keep = min(max_read_pairs, available_pairs)

    print(f"Writing {pairs_to_keep} read pairs for {sample_id}.")

    write_limited_fastq(temp_r1, output_r1, pairs_to_keep)
    write_limited_fastq(temp_r2, output_r2, pairs_to_keep)

    shutil.rmtree(temp_dir)

    return {
        "sample_id": sample_id,
        "r1": output_r1.name,
        "r2": output_r2.name,
        "genus": row.get("genus", ""),
        "species": row.get("species", ""),
        "source": row.get("source", "NCBI_SRA"),
    }


def write_output_manifest(output_manifest: Path, rows: list[dict[str, str]]) -> None:
    """Write a portable FASTQ fixture manifest.

    Args:
        output_manifest (Path): Path to output manifest.
        rows (list[dict[str, str]]): Manifest rows.

    Returns:
        None
    """

    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    columns = ["sample_id", "r1", "r2", "genus", "species", "source"]

    with output_manifest.open("w", encoding="utf-8") as handle:
        handle.write("\t".join(columns) + "\n")

        for row in rows:
            handle.write(
                "\t".join(str(row.get(column, "")) for column in columns) + "\n"
            )


def main() -> int:
    """Regenerate FASTQ fixtures from cached SRA files.

    Returns:
        int: Exit code.
    """

    args = parse_args()

    manifest_path = Path(args.manifest)
    sra_cache_dir = Path(args.sra_cache_dir)
    output_dir = Path(args.output_dir)
    output_manifest = Path(args.output_manifest)

    rows = read_manifest(manifest_path)
    output_rows = []

    for row in rows:
        output_row = regenerate_sample(
            row=row,
            sra_cache_dir=sra_cache_dir,
            output_dir=output_dir,
            max_read_pairs=args.max_read_pairs,
            threads=args.threads,
            overwrite=args.overwrite,
        )

        output_rows.append(output_row)

    write_output_manifest(output_manifest, output_rows)

    print(f"Wrote manifest: {output_manifest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())