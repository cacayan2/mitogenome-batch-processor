"""Download, validate, and initialize MITOS2 reference data."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

from mitopipeline.logging.logger_factory import make_logger

DB_SUFFIXES = (".phr", ".pin", ".psq")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refseqver", required=True)
    parser.add_argument("--refdir", required=True)
    parser.add_argument("--zenodo-record", default="4284483")
    parser.add_argument("--conda-env", required=True)
    parser.add_argument("--reference-ready-file", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def run_command(command: list[str], logger) -> subprocess.CompletedProcess:
    logger.debug("Command: %s", command)
    result = subprocess.run(command, capture_output=True, text=True)
    logger.debug("stdout:\n%s", result.stdout)
    logger.debug("stderr:\n%s", result.stderr)
    return result


def safe_extract(archive_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with tarfile.open(archive_path, "r:bz2") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if target != destination and destination not in target.parents:
                raise RuntimeError(f"Unsafe archive path: {member.name}")
        archive.extractall(destination)


def validate_reference_tree(refseq_path: Path) -> None:
    required = [
        refseq_path / "auxinfo.json",
        refseq_path / "featureProt",
        refseq_path / "featureNuc",
        refseq_path / "ncRNA",
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Missing MITOS2 reference component: {path}")


def db_needs_rebuild(fasta: Path) -> bool:
    parts = [Path(f"{fasta}{suffix}") for suffix in DB_SUFFIXES]
    if any(not part.is_file() for part in parts):
        return True
    mtimes = [fasta.stat().st_mtime, *(part.stat().st_mtime for part in parts)]
    return max(mtimes) - min(mtimes) > 60


def rebuild_db(fasta: Path, conda_env: str, logger) -> None:
    logger.info("Rebuilding MITOS2 protein BLAST database: %s", fasta.name)
    for suffix in DB_SUFFIXES:
        Path(f"{fasta}{suffix}").unlink(missing_ok=True)
    result = run_command(
        ["conda", "run", "-n", conda_env, "makeblastdb",
         "-in", str(fasta), "-dbtype", "prot"],
        logger,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to rebuild BLAST database: {fasta}")


def verify_db(fasta: Path, conda_env: str, logger) -> None:
    result = run_command(
        ["conda", "run", "-n", conda_env, "blastdbcmd",
         "-db", str(fasta), "-info"],
        logger,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Invalid MITOS2 BLAST database: {fasta}")


def initialize_databases(refseq_path: Path, conda_env: str, logger) -> int:
    fasta_files = sorted((refseq_path / "featureProt").glob("*.fas"))
    if not fasta_files:
        raise FileNotFoundError("No protein FASTA files found for MITOS2.")
    rebuilt = 0
    for fasta in fasta_files:
        if db_needs_rebuild(fasta):
            rebuild_db(fasta, conda_env, logger)
            rebuilt += 1
        verify_db(fasta, conda_env, logger)
    return rebuilt


def download_reference(refseqver: str, refdir: Path, record: str, logger) -> None:
    archive_name = f"{refseqver}.tar.bz2"
    url = f"https://zenodo.org/records/{record}/files/{archive_name}?download=1"
    refdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / archive_name
        extract_root = tmp_path / "extract"
        extract_root.mkdir()

        result = run_command(
            ["curl", "-L", "--fail", "--retry", "3",
             "--output", str(archive_path), url],
            logger,
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to download MITOS2 reference data.")

        safe_extract(archive_path, extract_root)
        extracted = extract_root / refseqver
        if not extracted.is_dir():
            raise FileNotFoundError(f"Archive did not contain {refseqver}.")

        destination = refdir / refseqver
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(extracted), str(destination))


def main() -> int:
    args = parse_args()
    logger = make_logger("mitos2_reference_data", args.log_file)
    refdir = Path(args.refdir).expanduser().resolve()
    refseq_path = refdir / args.refseqver
    ready_file = Path(args.reference_ready_file).expanduser().resolve()

    try:
        if args.overwrite and refseq_path.exists():
            shutil.rmtree(refseq_path)

        reference_requires_download = False

        if not refseq_path.exists():
            logger.info(
                "MITOS2 reference data are missing: %s",
                refseq_path,
            )
            reference_requires_download = True

        else:
            try:
                validate_reference_tree(refseq_path)

            except (FileNotFoundError, ValueError) as error:
                logger.warning(
                    "Existing MITOS2 reference data are incomplete or invalid: %s",
                    error,
                )
                logger.info(
                    "Removing incomplete MITOS2 reference directory: %s",
                    refseq_path,
                )

                shutil.rmtree(refseq_path)

                reference_requires_download = True


        if reference_requires_download:
            logger.info(
                "Downloading clean MITOS2 reference data: %s",
                args.refseqver,
            )

            download_reference(
                refseqver=args.refseqver,
                refdir=refdir,
                record=args.zenodo_record,
                logger=logger,
            )


        validate_reference_tree(refseq_path)

        rebuilt = initialize_databases(refseq_path, args.conda_env, logger)

        ready_file.parent.mkdir(parents=True, exist_ok=True)
        ready_file.write_text(
            f"refseqver={args.refseqver}\nrefdir={refdir}\n"
            f"protein_databases_rebuilt={rebuilt}\n",
            encoding="utf-8",
        )
        logger.info("MITOS2 reference data ready; rebuilt %d databases.", rebuilt)
        return 0

    except Exception as error:
        ready_file.unlink(missing_ok=True)
        logger.exception("MITOS2 reference setup failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
