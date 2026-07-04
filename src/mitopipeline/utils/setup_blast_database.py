"""setup_blast_database.py

Build and validate a local nucleotide BLAST database.
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


# Constants
NUCLEOTIDE_DATABASE_EXTENSIONS = [
    ".nhr",
    ".nin",
    ".nsq",
]

OPTIONAL_DATABASE_EXTENSIONS = [
    ".ndb",
    ".not",
    ".ntf",
    ".nto",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Build and validate a local nucleotide BLAST database."
    )

    parser.add_argument(
        "--input-fasta",
        required=True,
        help="Reference nucleotide FASTA used to build the database.",
    )
    parser.add_argument(
        "--database-prefix",
        required=True,
        help=(
            "Output BLAST database prefix, for example "
            "/data/blast/fish_mito."
        ),
    )
    parser.add_argument(
        "--database-title",
        default="mitopipeline mitochondrial reference database",
        help="Human-readable BLAST database title.",
    )
    parser.add_argument(
        "--done-file",
        required=True,
        help="Path to the Snakemake setup completion marker.",
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the setup log file.",
    )
    parser.add_argument(
        "--metadata-file",
        default=None,
        help=(
            "Optional database metadata JSON path. Defaults to "
            "<database-prefix>.metadata.json."
        ),
    )
    parser.add_argument(
        "--parse-seqids",
        action="store_true",
        help="Pass -parse_seqids to makeblastdb.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing or incomplete BLAST database.",
    )

    return parser.parse_args()


def run_command(
    command: list[str],
    logger,
) -> subprocess.CompletedProcess:
    """Run a command and capture its output.

    Args:
        command (list[str]): Command to execute.
        logger: Configured logger.

    Returns:
        subprocess.CompletedProcess: Completed process.
    """
    logger.debug(f"Command: {command}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    logger.debug(f"Return code: {result.returncode}")
    logger.debug(f"stdout: {result.stdout}")
    logger.debug(f"stderr: {result.stderr}")

    return result


def required_database_files(database_prefix: Path) -> list[Path]:
    """Return required nucleotide BLAST database files.

    Args:
        database_prefix (Path): BLAST database prefix.

    Returns:
        list[Path]: Required component paths.
    """
    prefix = str(database_prefix)

    return [
        Path(f"{prefix}{extension}")
        for extension in NUCLEOTIDE_DATABASE_EXTENSIONS
    ]


def database_files(database_prefix: Path) -> list[Path]:
    """Return all detected files belonging to a database prefix.

    Args:
        database_prefix (Path): BLAST database prefix.

    Returns:
        list[Path]: Matching database files.
    """
    parent = database_prefix.parent
    prefix_name = database_prefix.name

    if not parent.exists():
        return []

    return sorted(
        path
        for path in parent.glob(f"{prefix_name}.*")
        if path.is_file()
    )


def database_components_exist(database_prefix: Path) -> bool:
    """Return whether all required database files exist.

    Args:
        database_prefix (Path): BLAST database prefix.

    Returns:
        bool: True when required files exist.
    """
    return all(
        path.exists()
        for path in required_database_files(database_prefix)
    )


def validate_database(
    database_prefix: Path,
    logger,
) -> bool:
    """Validate a BLAST database using blastdbcmd.

    Args:
        database_prefix (Path): BLAST database prefix.
        logger: Configured logger.

    Returns:
        bool: True when the database is readable and valid.
    """
    if not database_components_exist(database_prefix):
        return False

    result = run_command(
        [
            "blastdbcmd",
            "-db",
            str(database_prefix),
            "-dbtype",
            "nucl",
            "-info",
        ],
        logger,
    )

    return result.returncode == 0


def remove_database_files(
    database_prefix: Path,
    logger,
) -> None:
    """Remove files associated with a BLAST database prefix.

    Args:
        database_prefix (Path): BLAST database prefix.
        logger: Configured logger.
    """
    for path in database_files(database_prefix):
        logger.info(f"Removing existing BLAST database file: {path}")
        path.unlink()


def build_database(
    input_fasta: Path,
    temporary_prefix: Path,
    database_title: str,
    parse_seqids: bool,
    logger,
) -> int:
    """Run makeblastdb.

    Args:
        input_fasta (Path): Reference FASTA.
        temporary_prefix (Path): Temporary output database prefix.
        database_title (str): Database title.
        parse_seqids (bool): Whether to parse sequence identifiers.
        logger: Configured logger.

    Returns:
        int: makeblastdb exit code.
    """
    command = [
        "makeblastdb",
        "-in",
        str(input_fasta),
        "-dbtype",
        "nucl",
        "-out",
        str(temporary_prefix),
        "-title",
        database_title,
    ]

    if parse_seqids:
        command.append("-parse_seqids")

    result = run_command(command, logger)

    return result.returncode


def install_database(
    temporary_prefix: Path,
    final_prefix: Path,
    logger,
) -> None:
    """Move completed database files into their final location.

    Args:
        temporary_prefix (Path): Temporary database prefix.
        final_prefix (Path): Final database prefix.
        logger: Configured logger.
    """
    temporary_files = database_files(temporary_prefix)

    if not temporary_files:
        raise FileNotFoundError(
            "No temporary BLAST database files were created."
        )

    final_prefix.parent.mkdir(parents=True, exist_ok=True)

    for source_path in temporary_files:
        suffix = source_path.name[len(temporary_prefix.name):]
        destination_path = Path(f"{final_prefix}{suffix}")

        logger.info(
            f"Installing BLAST database file: "
            f"{source_path} -> {destination_path}"
        )

        shutil.move(
            str(source_path),
            str(destination_path),
        )


def write_metadata(
    metadata_file: Path,
    input_fasta: Path,
    database_prefix: Path,
    database_title: str,
) -> None:
    """Write BLAST database setup metadata.

    Args:
        metadata_file (Path): Metadata JSON path.
        input_fasta (Path): Source FASTA.
        database_prefix (Path): Final database prefix.
        database_title (str): Database title.
    """
    metadata = {
        "database_type": "nucl",
        "database_title": database_title,
        "database_prefix": str(database_prefix.resolve()),
        "input_fasta": str(input_fasta.resolve()),
        "input_fasta_size_bytes": input_fasta.stat().st_size,
        "created_at": datetime.now().isoformat(),
    }

    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def write_done_file(
    done_file: Path,
    database_prefix: Path,
) -> None:
    """Write setup completion marker.

    Args:
        done_file (Path): Done-file path.
        database_prefix (Path): Database prefix.
    """
    done_file.parent.mkdir(parents=True, exist_ok=True)
    done_file.write_text(
        f"{database_prefix}\n",
        encoding="utf-8",
    )


def main() -> int:
    """Build and validate local BLAST database.

    Returns:
        int: Exit code.
    """
    args = parse_args()

    logger = make_logger(
        name="blast_database",
        log_file_path=args.log_file,
    )

    input_fasta = Path(args.input_fasta)
    database_prefix = Path(args.database_prefix)
    done_file = Path(args.done_file)

    metadata_file = (
        Path(args.metadata_file)
        if args.metadata_file is not None
        else Path(f"{database_prefix}.metadata.json")
    )

    logger.info(
        f"Initializing BLAST database: {database_prefix}"
    )
    logger.debug(
        f"Reference FASTA: {input_fasta}"
    )

    # Validating source FASTA.
    if not input_fasta.exists():
        logger.error(
            f"Reference FASTA does not exist: {input_fasta}"
        )
        return 1

    if not input_fasta.is_file():
        logger.error(
            f"Reference FASTA is not a file: {input_fasta}"
        )
        return 1

    if input_fasta.stat().st_size == 0:
        logger.error(
            f"Reference FASTA is empty: {input_fasta}"
        )
        return 1

    existing_files = database_files(database_prefix)
    complete_database = database_components_exist(database_prefix)

    # Skipping when a valid database already exists.
    if complete_database and not args.overwrite:
        logger.info(
            f"Existing BLAST database detected: {database_prefix}"
        )

        if validate_database(database_prefix, logger):
            logger.info(
                f"Existing BLAST database is valid: {database_prefix}"
            )
            write_done_file(done_file, database_prefix)
            return 0

        logger.error(
            "Existing BLAST database files were detected, but the database "
            "failed validation. Use --overwrite to rebuild it."
        )
        return 1

    # Refusing partial existing databases unless overwrite was requested.
    if existing_files and not complete_database and not args.overwrite:
        logger.error(
            "Incomplete BLAST database files were detected: "
            f"{existing_files}. Use --overwrite to rebuild the database."
        )
        return 1

    # Removing existing files when rebuilding.
    if existing_files and args.overwrite:
        remove_database_files(database_prefix, logger)

    database_prefix.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Building into a temporary directory.
    with tempfile.TemporaryDirectory(
        dir=database_prefix.parent
    ) as temporary_directory:
        temporary_directory_path = Path(temporary_directory)
        temporary_prefix = (
            temporary_directory_path / database_prefix.name
        )

        logger.info(
            f"Building nucleotide BLAST database from {input_fasta}."
        )

        return_code = build_database(
            input_fasta=input_fasta,
            temporary_prefix=temporary_prefix,
            database_title=args.database_title,
            parse_seqids=args.parse_seqids,
            logger=logger,
        )

        if return_code != 0:
            logger.error(
                f"makeblastdb failed with return code {return_code}."
            )
            return return_code

        # Validating before installation.
        if not validate_database(temporary_prefix, logger):
            logger.error(
                "Temporary BLAST database failed validation."
            )
            return 1

        try:
            install_database(
                temporary_prefix=temporary_prefix,
                final_prefix=database_prefix,
                logger=logger,
            )
        except (FileNotFoundError, OSError) as error:
            logger.exception(
                f"Failed to install BLAST database: {error}"
            )
            return 1

    # Final validation.
    if not validate_database(database_prefix, logger):
        logger.error(
            f"Installed BLAST database failed validation: "
            f"{database_prefix}"
        )
        return 1

    write_metadata(
        metadata_file=metadata_file,
        input_fasta=input_fasta,
        database_prefix=database_prefix,
        database_title=args.database_title,
    )

    write_done_file(
        done_file=done_file,
        database_prefix=database_prefix,
    )

    logger.info(
        f"BLAST database initialized successfully: {database_prefix}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())