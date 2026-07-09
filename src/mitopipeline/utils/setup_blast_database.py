"""setup_blast_database.py

Build, download, update, and validate a local nucleotide BLAST database.

For MitoPipeline, ``database_source: ncbi`` means:
1. query NCBI nucleotide through Entrez for mitochondrial references;
2. write those records to reference_fasta;
3. build a local BLAST database from that FASTA.

This avoids attempting to download enormous preformatted NCBI databases such
as refseq_genomic.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


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

    parser.add_argument(
        "--entrez-email",
        default=None,
    )
    parser.add_argument(
        "--entrez-api-key",
        default=None,
    )
    parser.add_argument(
        "--ncbi-query",
        default=(
            'mitochondrion[filter] AND refseq[filter] '
            'AND "complete genome"[Title]'
        ),
    )
    parser.add_argument(
        "--ncbi-max-records",
        type=int,
        default=250,
    )
    parser.add_argument(
        "--ncbi-batch-size",
        type=int,
        default=50,
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


def fetch_url_text(
    url: str,
    logger,
    retries: int = 3,
    delay_seconds: float = 1.0,
) -> str:
    """Fetch text from a URL with simple retry handling."""
    for attempt in range(1, retries + 1):
        try:
            logger.debug(f"Fetching URL attempt {attempt}: {url}")
            with urllib.request.urlopen(
                url,
                timeout=120,
            ) as response:
                return response.read().decode(
                    "utf-8"
                )

        except Exception as error:
            logger.warning(
                f"URL fetch failed on attempt {attempt}/{retries}: "
                f"{error}"
            )
            if attempt == retries:
                raise
            time.sleep(delay_seconds * attempt)

    raise RuntimeError("Unreachable URL retry state.")


def ncbi_esearch(
    query: str,
    email: str,
    api_key: str | None,
    max_records: int,
    logger,
) -> list[str]:
    """Search NCBI nucleotide and return record IDs."""
    parameters = {
        "db": "nuccore",
        "term": query,
        "retmode": "xml",
        "retmax": str(max_records),
        "email": email,
        "tool": "mitopipeline",
    }

    if api_key:
        parameters["api_key"] = api_key

    url = (
        f"{EUTILS_BASE}/esearch.fcgi?"
        + urllib.parse.urlencode(parameters)
    )

    text = fetch_url_text(
        url,
        logger=logger,
    )

    root = ET.fromstring(text)

    ids = [
        element.text
        for element in root.findall(".//IdList/Id")
        if element.text
    ]

    count_text = root.findtext(".//Count")
    logger.info(
        f"NCBI Entrez query matched {count_text or 'unknown'} records; "
        f"retrieving {len(ids)}."
    )

    return ids


def ncbi_efetch_fasta(
    ids: list[str],
    email: str,
    api_key: str | None,
    batch_size: int,
    logger,
) -> str:
    """Fetch nucleotide FASTA records from NCBI."""
    fasta_chunks: list[str] = []

    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]

        parameters = {
            "db": "nuccore",
            "id": ",".join(batch),
            "rettype": "fasta",
            "retmode": "text",
            "email": email,
            "tool": "mitopipeline",
        }

        if api_key:
            parameters["api_key"] = api_key

        url = (
            f"{EUTILS_BASE}/efetch.fcgi?"
            + urllib.parse.urlencode(parameters)
        )

        logger.info(
            f"Fetching NCBI FASTA records {start + 1}-"
            f"{start + len(batch)} of {len(ids)}."
        )

        fasta_chunks.append(
            fetch_url_text(
                url,
                logger=logger,
            )
        )

        # Be polite to NCBI when no API key is configured.
        if not api_key:
            time.sleep(0.4)

    return "\n".join(
        chunk.strip()
        for chunk in fasta_chunks
        if chunk.strip()
    ) + "\n"


def count_fasta_records(
    fasta_path: Path,
) -> int:
    """Count FASTA records."""
    count = 0

    with fasta_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for line in handle:
            if line.startswith(">"):
                count += 1

    return count


def download_ncbi_reference_fasta(
    reference_fasta: Path,
    query: str,
    email: str,
    api_key: str | None,
    max_records: int,
    batch_size: int,
    overwrite: bool,
    logger,
) -> int:
    """Download mitochondrial reference sequences from NCBI Entrez."""
    if reference_fasta.exists() and not overwrite:
        record_count = count_fasta_records(
            reference_fasta
        )
        if record_count > 0:
            logger.info(
                f"Existing NCBI reference FASTA found with "
                f"{record_count} records: {reference_fasta}"
            )
            return 0

    if not email:
        logger.error(
            "NCBI Entrez download requires --entrez-email."
        )
        return 1

    reference_fasta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ids = ncbi_esearch(
        query=query,
        email=email,
        api_key=api_key,
        max_records=max_records,
        logger=logger,
    )

    if not ids:
        logger.error(
            f"NCBI query returned no records: {query}"
        )
        return 1

    fasta_text = ncbi_efetch_fasta(
        ids=ids,
        email=email,
        api_key=api_key,
        batch_size=batch_size,
        logger=logger,
    )

    if not fasta_text.strip():
        logger.error(
            "NCBI efetch returned an empty FASTA response."
        )
        return 1

    temporary_fasta = reference_fasta.with_suffix(
        reference_fasta.suffix + ".tmp"
    )
    temporary_fasta.write_text(
        fasta_text,
        encoding="utf-8",
    )

    record_count = count_fasta_records(
        temporary_fasta
    )

    if record_count == 0:
        logger.error(
            "Downloaded reference FASTA contains zero FASTA records."
        )
        temporary_fasta.unlink(
            missing_ok=True,
        )
        return 1

    shutil.move(
        str(temporary_fasta),
        str(reference_fasta),
    )

    logger.info(
        f"Wrote {record_count} NCBI mitochondrial references to "
        f"{reference_fasta}."
    )

    return 0


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


def write_metadata(
    metadata_file: Path,
    database_source: str,
    database_name: str,
    database_prefix: Path,
    reference_fasta: Path | None = None,
    ncbi_query: str | None = None,
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
        metadata["reference_fasta_record_count"] = count_fasta_records(
            reference_fasta
        )

    if ncbi_query is not None:
        metadata["ncbi_query"] = ncbi_query

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
    database_source: str = "fasta",
    ncbi_query: str | None = None,
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
        database_source=database_source,
        database_name=database_prefix.name,
        database_prefix=database_prefix,
        reference_fasta=reference_fasta,
        ncbi_query=ncbi_query,
    )
    write_done_file(
        done_file,
        database_prefix,
    )

    return 0


def setup_ncbi_mitochondrial_database(
    reference_fasta: Path,
    database_prefix: Path,
    database_title: str,
    parse_seqids: bool,
    overwrite: bool,
    metadata_file: Path,
    done_file: Path,
    entrez_email: str,
    entrez_api_key: str | None,
    ncbi_query: str,
    ncbi_max_records: int,
    ncbi_batch_size: int,
    logger,
) -> int:
    """Download NCBI mitochondrial references and build local BLAST DB."""
    reference_return_code = download_ncbi_reference_fasta(
        reference_fasta=reference_fasta,
        query=ncbi_query,
        email=entrez_email,
        api_key=entrez_api_key,
        max_records=ncbi_max_records,
        batch_size=ncbi_batch_size,
        overwrite=overwrite,
        logger=logger,
    )

    if reference_return_code != 0:
        return reference_return_code

    return setup_fasta_database(
        reference_fasta=reference_fasta,
        database_prefix=database_prefix,
        database_title=database_title,
        parse_seqids=parse_seqids,
        overwrite=overwrite,
        metadata_file=metadata_file,
        done_file=done_file,
        logger=logger,
        database_source="ncbi_entrez_fasta",
        ncbi_query=ncbi_query,
    )


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

        return setup_ncbi_mitochondrial_database(
            reference_fasta=reference_fasta,
            database_prefix=database_prefix,
            database_title=args.database_title,
            parse_seqids=args.parse_seqids,
            overwrite=args.overwrite,
            metadata_file=metadata_file,
            done_file=done_file,
            entrez_email=args.entrez_email,
            entrez_api_key=args.entrez_api_key,
            ncbi_query=args.ncbi_query,
            ncbi_max_records=args.ncbi_max_records,
            ncbi_batch_size=args.ncbi_batch_size,
            logger=logger,
        )

    except Exception as error:
        logger.exception(
            f"BLAST database setup failed: {error}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
