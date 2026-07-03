"""setup_mitos2_reference_data.py

Download and initialize MITOS2 reference data.
"""

# Imports
import argparse
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    # Initializing the parser.
    parser = argparse.ArgumentParser(
        description="Download and initialize MITOS2 reference data."
    )

    # Adding arguments.
    parser.add_argument("--refseqver", required=True, help="MITOS2 reference version.")
    parser.add_argument("--refdir", required=True, help="Base MITOS2 reference directory.")
    parser.add_argument("--zenodo-record", default="4284483", help="Zenodo record ID.")
    parser.add_argument("--done-file", required=True, help="Path to the done file.")
    parser.add_argument("--log-file", required=True, help="Path to the log file.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing reference data.")

    # Returning parsed arguments.
    return parser.parse_args()


def run_command(command: list[str], logger) -> subprocess.CompletedProcess:
    """Run a command and return the completed process.

    Args:
        command (list[str]): Command to run.
        logger: Logger object.

    Returns:
        subprocess.CompletedProcess: Completed process object.
    """

    # Logging command.
    logger.debug(f"Command: {command}")

    # Running command.
    result = subprocess.run(command, capture_output=True, text=True)

    # Logging output.
    logger.debug(f"stdout: {result.stdout}")
    logger.debug(f"stderr: {result.stderr}")

    # Returning result.
    return result


def main() -> int:
    """Download and initialize MITOS2 reference data.

    Returns:
        int: Exit code.
    """

    # Parsing command-line arguments.
    args = parse_args()

    # Creating logger.
    logger = make_logger(
        name="mitos2_reference_data",
        log_file_path=args.log_file,
    )

    # Resolving paths.
    refdir = Path(args.refdir)
    refseq_path = refdir / args.refseqver
    done_file = Path(args.done_file)

    # Constructing archive information.
    archive_name = f"{args.refseqver}.tar.bz2"
    download_url = (
        f"https://zenodo.org/records/{args.zenodo_record}/files/"
        f"{archive_name}?download=1"
    )

    # Logging setup.
    logger.info(f"Initializing MITOS2 reference data: {args.refseqver}")
    logger.debug(f"Reference root: {refdir}")
    logger.debug(f"Reference path: {refseq_path}")
    logger.debug(f"Download URL: {download_url}")

    # Creating reference root.
    refdir.mkdir(parents=True, exist_ok=True)

    # Skipping if reference data already exists.
    if refseq_path.exists() and not args.overwrite:
        logger.info(f"MITOS2 reference data already exists: {refseq_path}")

        # Creating done file.
        done_file.parent.mkdir(parents=True, exist_ok=True)
        done_file.write_text(f"{args.refseqver}\n", encoding="utf-8")

        return 0

    # Removing existing reference data if overwrite is requested.
    if refseq_path.exists() and args.overwrite:
        logger.info(f"Removing existing MITOS2 reference data: {refseq_path}")
        shutil.rmtree(refseq_path)

    # Downloading and extracting in a temporary directory.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        archive_path = tmp_dir / archive_name

        # Downloading archive.
        logger.info(f"Downloading MITOS2 reference archive: {archive_name}")

        result = run_command(
            [
                "curl",
                "-L",
                "--fail",
                "--retry",
                "3",
                "--output",
                str(archive_path),
                download_url,
            ],
            logger,
        )

        if result.returncode != 0:
            logger.error(f"Failed to download MITOS2 reference data: {args.refseqver}")
            return result.returncode

        # Extracting archive.
        logger.info(f"Extracting MITOS2 reference archive: {archive_path}")

        try:
            with tarfile.open(archive_path, "r:bz2") as archive:
                archive.extractall(refdir)
        except tarfile.TarError as error:
            logger.error(f"Failed to extract MITOS2 reference archive: {error}")
            return 1

    # Validating expected reference directory.
    if not refseq_path.exists():
        logger.error(f"Expected MITOS2 reference directory was not created: {refseq_path}")
        return 1

    # Validating key reference files/directories.
    required_paths = [
        refseq_path / "auxinfo.json",
        refseq_path / "featureProt",
        refseq_path / "featureNuc",
        refseq_path / "ncRNA",
    ]

    for required_path in required_paths:
        if not required_path.exists():
            logger.error(f"Missing MITOS2 reference component: {required_path}")
            return 1

    # Creating done file.
    done_file.parent.mkdir(parents=True, exist_ok=True)
    done_file.write_text(f"{args.refseqver}\n", encoding="utf-8")

    # Logging success.
    logger.info(f"MITOS2 reference data initialized: {refseq_path}")

    # Returning success.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())