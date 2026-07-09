"""Create/verify MITOS2 and prepare its references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-name", default="mito-annotation")
    parser.add_argument("--env-file", default="envs/annotation.yaml")
    parser.add_argument("--refseqver", default="refseq89m")
    parser.add_argument("--refdir", default="resources/mitos")
    parser.add_argument("--zenodo-record", default="4284483")
    parser.add_argument("--reference-ready-file", required=True)
    parser.add_argument("--done-file", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--overwrite-reference", action="store_true")
    return parser.parse_args()


def run_command(command: list[str], logger) -> subprocess.CompletedProcess:
    logger.debug("Command: %s", command)
    result = subprocess.run(command, capture_output=True, text=True)
    logger.debug("stdout:\n%s", result.stdout)
    logger.debug("stderr:\n%s", result.stderr)
    return result


def env_exists(name: str, logger) -> bool:
    result = run_command(["conda", "env", "list", "--json"], logger)
    if result.returncode != 0:
        return False
    return any(Path(path).name == name for path in json.loads(result.stdout).get("envs", []))


def create_env(name: str, env_file: Path, logger) -> None:
    if not env_file.is_file():
        raise FileNotFoundError(f"MITOS2 environment file missing: {env_file}")
    result = run_command(
        ["conda", "env", "create", "-n", name, "-f", str(env_file)],
        logger,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create MITOS2 environment: {name}")


def resolve_executable(name: str, logger) -> str:
    for executable in ("runmitos", "runmitos.py"):
        result = run_command(
            ["conda", "run", "-n", name, executable, "--help"],
            logger,
        )
        if result.returncode == 0:
            return executable
    raise RuntimeError("Neither runmitos nor runmitos.py is available.")


def main() -> int:
    args = parse_args()
    logger = make_logger("mitos2_setup", args.log_file)
    done_file = Path(args.done_file).resolve()
    ready_file = Path(args.reference_ready_file).resolve()

    try:
        if shutil.which("conda") is None:
            raise RuntimeError("Conda was not found on PATH.")

        if not env_exists(args.env_name, logger):
            create_env(args.env_name, Path(args.env_file), logger)
        else:
            logger.info("MITOS2 environment already exists: %s", args.env_name)

        executable = resolve_executable(args.env_name, logger)

        command = [
            "python", "-m", "mitopipeline.utils.setup_mitos2_reference_data",
            "--refseqver", args.refseqver,
            "--refdir", str(Path(args.refdir).resolve()),
            "--zenodo-record", args.zenodo_record,
            "--conda-env", args.env_name,
            "--reference-ready-file", str(ready_file),
            "--log-file", str(Path(args.log_file).resolve()),
        ]
        if args.overwrite_reference:
            command.append("--overwrite")

        result = run_command(command, logger)
        if result.returncode != 0:
            raise RuntimeError("MITOS2 reference setup failed.")

        done_file.parent.mkdir(parents=True, exist_ok=True)
        done_file.write_text(
            f"env_name={args.env_name}\nexecutable={executable}\n"
            f"refseqver={args.refseqver}\nrefdir={Path(args.refdir).resolve()}\n",
            encoding="utf-8",
        )
        logger.info("MITOS2 setup completed successfully.")
        return 0

    except Exception as error:
        done_file.unlink(missing_ok=True)
        logger.exception("MITOS2 setup failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
