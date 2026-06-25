"""setup_getorganelle_database.py

Initialize GetOrganelle databases.
"""

# Imports
import argparse
import subprocess
from pathlib import Path
from mitopipeline.logging.logger_factory import make_logger

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    # Initializing the argparse object.
    parser = argparse.ArgumentParser(description = "Initialize GetOrganelle databases.")
    parser.add_argument("--database-type", required = True, help = "Type of database to initialize.")
    parser.add_argument("--done-file", required = True, help = "Path to the done file.")
    parser.add_argument("--log-file", required = True, help = "Path to the logger.")

    return parser.parse_args()

def main() -> int:
    """Main function of the script.
    
    Returns:
        int: Exit code of the script.
    """
    # Parsing command-line arguments.
    args = parse_args()

    # Constructing the logger.
    logger = make_logger(name = "getorganelle", log_file_path = args.log_file)

    # Constructing command to build database.
    command = [
        "get_organelle_config.py",
        "-a",
        args.database_type
    ]

    # Logging the command.
    logger.info(f"Initializing GetOrganelle database: {args.database_type}")
    logger.debug(f"Command: {command}")

    # Running command.
    result = subprocess.run(command, capture_output = True, text = True)

    # Logging output.
    logger.debug(f"stdout: {result.stdout}")
    logger.debug(f"stderr: {result.stderr}")

    # Checking initializtion was successful.
    if result.returncode != 0:
        logger.error(f"Failed to initialize GetOrganelle database: {args.database_type}")
        return result.returncode
    
    # Creating done file.
    done_file = Path(args.done_file)
    done_file.parent.mkdir(parents = True, exist_ok = True)
    done_file.write_text(f"{args.database_type}\n", encoding = "utf-8")

    # Logging and returning.
    logger.info(f"GetOrganelle database initialized: {args.database_type}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
