"""setup_blast_database.py

Build, download, update, and validate a local nucleotide BLAST database.
"""

# Imports
import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Set up a local nucleotide BLAST database."
    )

    parser.add_argument(
        "--database-source",
        required=True,
        choices=["ncbi", "fasta"],
    )
    parser.add_argument(
        "--database-name",
        required=True,
    )
    parser.add_argument(
        "--database-dir",
        required=True,
    )
    parser.add_argument(
        "--reference-fasta",
        required=True,
    )
    parser.add_argument(
        "--database-title",
        required=True,
    )
    parser.add_argument(
        "--done-file",
        required=True,
    )
    parser.add_argument(
        "--metadata-file",
        required=True,
    )
    parser.add_argument(
        "--log-file",
        required=True,
    )
    parser.add_argument(
        "--parse-seqids",
        action="store_true",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
    )

    return parser.parse_args()


def run_command(
    command: list[str],
    logger,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run a command and capture output."""
    logger.debug(f"Command: {command}")
    logger.debug(f"Working directory: {cwd}")

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    logger.debug(f"Return code: {result.returncode}")
    logger.debug(f"stdout: {result.stdout}")
    logger.debug(f"stderr: {result.stderr}")

    return result


def database_files(
    database_prefix: Path,
) -> list[Path]:
    """Return all files associated with a database prefix."""
    if not database_prefix.parent.exists():
        return []

    return sorted(
        path
        for path in database_prefix.parent.glob(
            f"{database_prefix.name}*"
        )
        if path.is_file()
    )


def validate_database(
    database_prefix: Path,
    logger,
) -> bool:
    """Validate a BLAST database using blastdbcmd."""
    result = run_command(
        [
            "blastdbcmd",
            "-db",
            str(database_prefix),
            "-dbtype",
            "nucl",
            "-info",
        ],
        logger=logger,
    )

    return result.returncode == 0


def remove_database_files(
    database_prefix: Path,
    logger,
) -> None:
    """Remove all files associated with a database prefix."""
    for path in database_files(database_prefix):
        logger.info(
            f"Removing BLAST database file: {path}"
        )
        path.unlink()


def validate_reference_fasta(
    reference_fasta: Path,
    logger,
) -> bool:
    """Validate custom reference FASTA."""
    if not reference_fasta.exists():
        logger.error(
            f"Reference FASTA does not exist: {reference_fasta}"
        )
        return False

    if not reference_fasta.is_file():
        logger.error(
            f"Reference FASTA is not a file: {reference_fasta}"
        )
        return False

    if reference_fasta.stat().st_size == 0:
        logger.error(
            f"Reference FASTA is empty: {reference_fasta}"
        )
        return False

    return True


def build_fasta_database(
    reference_fasta: Path,
    database_prefix: Path,
    database_title: str,
    parse_seqids: bool,
    logger,
) -> int:
    """Build a custom BLAST database from FASTA."""
    database_prefix.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(
        dir=database_prefix.parent,
    ) as temporary_directory:
        temporary_prefix = (
            Path(temporary_directory)
            / database_prefix.name
        )

        command = [
            "makeblastdb",
            "-in",
            str(reference_fasta),
            "-dbtype",
            "nucl",
            "-out",
            str(temporary_prefix),
            "-title",
            database_title,
        ]

        if parse_seqids:
            command.append("-parse_seqids")

        result = run_command(
            command,
            logger=logger,
        )

        if result.returncode != 0:
            return result.returncode

        if not validate_database(
            temporary_prefix,
            logger,
        ):
            logger.error(
                "Temporary BLAST database failed validation."
            )
            return 1

        for source_path in database_files(
            temporary_prefix
        ):
            suffix = source_path.name[
                len(temporary_prefix.name):
            ]

            destination_path = Path(
                f"{database_prefix}{suffix}"
            )

            shutil.move(
                str(source_path),
                str(destination_path),
            )

    return 0


def download_ncbi_database(
    database_name: str,
    database_dir: Path,
    logger,
) -> int:
    """Download or update an official NCBI BLAST database."""
    database_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = run_command(
        [
            "update_blastdb.pl",
            "--decompress",
            database_name,
        ],
        logger=logger,
        cwd=database_dir,
    )

    return result.returncode


def write_metadata(
    metadata_file: Path,
    database_source: str,
    database_name: str,
    database_prefix: Path,
    reference_fasta: Path | None = None,
) -> None:
    """Write database setup metadata."""
    metadata = {
        "database_type": "nucl",
        "database_source": database_source,
        "database_name": database_name,
        "database_prefix": str(
            database_prefix.resolve()
        ),
        "created_at": datetime.now().isoformat(),
    }

    if reference_fasta is not None:
        metadata["reference_fasta"] = str(
            reference_fasta.resolve()
        )
        metadata["reference_fasta_size_bytes"] = (
            reference_fasta.stat().st_size
        )

    metadata_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    metadata_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def write_done_file(
    done_file: Path,
    database_prefix: Path,
) -> None:
    """Write database setup completion marker."""
    done_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    done_file.write_text(
        f"{database_prefix}\n",
        encoding="utf-8",
    )


def setup_fasta_database(
    reference_fasta: Path,
    database_prefix: Path,
    database_title: str,
    parse_seqids: bool,
    overwrite: bool,
    metadata_file: Path,
    done_file: Path,
    logger,
) -> int:
    """Set up a local custom FASTA database."""
    if not validate_reference_fasta(
        reference_fasta,
        logger,
    ):
        return 1

    if (
        not overwrite
        and validate_database(database_prefix, logger)
    ):
        logger.info(
            f"Existing BLAST database is valid: "
            f"{database_prefix}"
        )
        write_done_file(
            done_file,
            database_prefix,
        )
        return 0

    existing_files = database_files(
        database_prefix
    )

    if existing_files and not overwrite:
        logger.error(
            "Existing BLAST database files failed validation. "
            "Use overwrite_database: true to rebuild them."
        )
        return 1

    if existing_files:
        remove_database_files(
            database_prefix,
            logger,
        )

    return_code = build_fasta_database(
        reference_fasta=reference_fasta,
        database_prefix=database_prefix,
        database_title=database_title,
        parse_seqids=parse_seqids,
        logger=logger,
    )

    if return_code != 0:
        return return_code

    if not validate_database(
        database_prefix,
        logger,
    ):
        logger.error(
            "Installed BLAST database failed validation."
        )
        return 1

    write_metadata(
        metadata_file=metadata_file,
        database_source="fasta",
        database_name=database_prefix.name,
        database_prefix=database_prefix,
        reference_fasta=reference_fasta,
    )
    write_done_file(
        done_file,
        database_prefix,
    )

    return 0


def setup_ncbi_database(
    database_name: str,
    database_prefix: Path,
    database_dir: Path,
    overwrite: bool,
    metadata_file: Path,
    done_file: Path,
    logger,
) -> int:
    """Set up an official preformatted NCBI database."""
    if (
        not overwrite
        and validate_database(database_prefix, logger)
    ):
        logger.info(
            f"Existing NCBI BLAST database is valid: "
            f"{database_prefix}"
        )
        write_done_file(
            done_file,
            database_prefix,
        )
        return 0

    if overwrite:
        remove_database_files(
            database_prefix,
            logger,
        )

    return_code = download_ncbi_database(
        database_name=database_name,
        database_dir=database_dir,
        logger=logger,
    )

    if return_code != 0:
        return return_code

    if not validate_database(
        database_prefix,
        logger,
    ):
        logger.error(
            f"Downloaded NCBI database failed validation: "
            f"{database_prefix}"
        )
        return 1

    write_metadata(
        metadata_file=metadata_file,
        database_source="ncbi",
        database_name=database_name,
        database_prefix=database_prefix,
    )
    write_done_file(
        done_file,
        database_prefix,
    )

    return 0


def main() -> int:
    """Set up selected local BLAST database."""
    args = parse_args()

    logger = make_logger(
        name="blast_database",
        log_file_path=args.log_file,
    )

    database_dir = Path(args.database_dir)
    database_prefix = (
        database_dir
        / args.database_name
    )
    reference_fasta = Path(
        args.reference_fasta
    )
    metadata_file = Path(
        args.metadata_file
    )
    done_file = Path(
        args.done_file
    )

    logger.info(
        f"Initializing {args.database_source} BLAST database: "
        f"{database_prefix}"
    )

    try:
        if args.database_source == "fasta":
            return setup_fasta_database(
                reference_fasta=reference_fasta,
                database_prefix=database_prefix,
                database_title=args.database_title,
                parse_seqids=args.parse_seqids,
                overwrite=args.overwrite,
                metadata_file=metadata_file,
                done_file=done_file,
                logger=logger,
            )

        return setup_ncbi_database(
            database_name=args.database_name,
            database_prefix=database_prefix,
            database_dir=database_dir,
            overwrite=args.overwrite,
            metadata_file=metadata_file,
            done_file=done_file,
            logger=logger,
        )

    except Exception as error:
        logger.exception(
            f"BLAST database setup failed: {error}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())