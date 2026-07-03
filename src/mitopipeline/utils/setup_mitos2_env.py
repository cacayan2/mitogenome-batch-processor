"""setup_mitos2_env.py

Set up MITOS2 for mitopipeline annotation. 
"""

# Imports
import argparse
import shutil
import subprocess
from pathlib import Path
from mitopipeline.logging.logger_factory import make_logger

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    # Initializing parser object.
    parser = argparse.ArgumentParser(description =  "Set up MITOS2 annotation environment.")

    # Adding arguments. 
    parser.add_argument("--env-name", default="mito-annotation", help="MITOS2 Conda environment name.")
    parser.add_argument("--env-file", default="envs/annotation.yaml", help="Path to MITOS2 environment YAML.")
    parser.add_argument("--refseqver", default="refseq89m", help="MITOS2 reference version.")
    parser.add_argument("--refdir", default="resources/mitos", help="MITOS2 reference root directory.")
    parser.add_argument("--zenodo-record", default="4284483", help="Zenodo record ID.")
    parser.add_argument("--done-file", required=True, help="Path to setup done file.")
    parser.add_argument("--log-file", required=True, help="Path to setup log file.")
    parser.add_argument("--overwrite-reference", action="store_true", help="Overwrite MITOS2 reference data.")

    # Returning parsed arguments.
    return parser.parse_args()

def run_command(command: list[str], logger) -> subprocess.CompletedProcess:
    """Run a command and capture output.

    Args:
        command (list[str]): Command to run.
        logger (logging.Logger): Logger object.

    Returns:
        subprocess.CompletedProcess: Result of the command execution.
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

def conda_exists() -> bool:
    """Return True if Conda is available.
    
    Returns:
        bool: True if Conda is available, False otherwise.
    """
    return shutil.which("conda") is not None

def conda_env_exists(env_name: str, logger) -> bool:
    """Return True if a Conda environment exists.

    Args:
        env_name (str): Conda environment name.
        logger: Logger object.

    Returns:
        bool: True if environment exists.
    """
    # Listing conda environments.
    result = run_command(["conda", "env", "list"], logger)

    # If conda env list fails, treat as unavailable.
    if result.returncode != 0:
        return False

    # Checking first column for environment name.
    for line in result.stdout.splitlines():
        parts = line.split()

        if len(parts) > 0 and parts[0] == env_name:
            return True

    return False


def create_conda_env(env_name: str, env_file: Path, logger) -> None:
    """Create the MITOS2 Conda environment.

    Args:
        env_name (str): Conda environment name.
        env_file (Path): Path to environment YAML.
        logger: Logger object.
    """
    # Checking environment file.
    if not env_file.exists():
        raise FileNotFoundError(f"MITOS2 environment file does not exist: {env_file}")

    # Creating environment.
    logger.info(f"Creating MITOS2 Conda environment: {env_name}")

    result = run_command(
        [
            "conda",
            "env",
            "create",
            "-f",
            str(env_file),
        ],
        logger,
    )

    # Checking command success.
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create MITOS2 Conda environment: {env_name}")


def verify_mitos2(env_name: str, logger) -> None:
    """Verify that MITOS2 can be called from the Conda environment.

    Args:
        env_name (str): Conda environment name.
        logger: Logger object.
    """
    # Running MITOS2 help command.
    logger.info(f"Verifying MITOS2 executable in Conda environment: {env_name}")

    result = run_command(
        [
            "conda",
            "run",
            "-n",
            env_name,
            "runmitos.py",
            "--help",
        ],
        logger,
    )

    # Checking command success.
    if result.returncode != 0:
        raise RuntimeError(f"MITOS2 verification failed in Conda environment: {env_name}")


def setup_reference_data(
    refseqver: str,
    refdir: Path,
    zenodo_record: str,
    done_file: Path,
    log_file: Path,
    overwrite_reference: bool,
    logger,
) -> None:
    """Run the MITOS2 reference data setup utility.

    Args:
        refseqver (str): MITOS2 reference version.
        refdir (Path): MITOS2 reference root.
        zenodo_record (str): Zenodo record ID.
        done_file (Path): Done file path.
        log_file (Path): Log file path.
        overwrite_reference (bool): Whether to overwrite reference data.
        logger: Logger object.
    """
    # Building setup command.
    command = [
        "python",
        "-m",
        "mitopipeline.utils.setup_mitos2_reference_data",
        "--refseqver",
        refseqver,
        "--refdir",
        str(refdir),
        "--zenodo-record",
        zenodo_record,
        "--done-file",
        str(done_file),
        "--log-file",
        str(log_file),
    ]

    # Adding overwrite flag if requested.
    if overwrite_reference:
        command.append("--overwrite")

    # Running setup command.
    logger.info("Setting up MITOS2 reference data.")
    result = run_command(command, logger)

    # Checking command success.
    if result.returncode != 0:
        raise RuntimeError("MITOS2 reference data setup failed.")


def main() -> int:
    """Set up MITOS2 for pipeline use.

    Returns:
        int: Exit code.
    """
    # Parsing arguments.
    args = parse_args()

    # Building paths.
    env_file = Path(args.env_file)
    refdir = Path(args.refdir)
    done_file = Path(args.done_file)
    log_file = Path(args.log_file)

    # Creating logger.
    logger = make_logger(name="mitos2_setup", log_file_path=log_file)

    try:
        # Checking Conda.
        if not conda_exists():
            raise RuntimeError("Conda was not found on PATH.")

        # Creating environment if missing.
        if conda_env_exists(args.env_name, logger):
            logger.info(f"MITOS2 Conda environment already exists: {args.env_name}")
        else:
            create_conda_env(args.env_name, env_file, logger)

        # Verifying MITOS2.
        verify_mitos2(args.env_name, logger)

        # Setting up reference data.
        setup_reference_data(
            refseqver=args.refseqver,
            refdir=refdir,
            zenodo_record=args.zenodo_record,
            done_file=done_file,
            log_file=log_file,
            overwrite_reference=args.overwrite_reference,
            logger=logger,
        )

        # Writing final setup done file.
        done_file.parent.mkdir(parents=True, exist_ok=True)
        done_file.write_text(
            f"env_name={args.env_name}\nrefseqver={args.refseqver}\nrefdir={refdir}\n",
            encoding="utf-8",
        )

        logger.info("MITOS2 setup completed successfully.")
        return 0

    except Exception as error:
        logger.exception(f"MITOS2 setup failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())