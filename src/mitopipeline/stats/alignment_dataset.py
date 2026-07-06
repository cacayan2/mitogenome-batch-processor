"""alignment_dataset.py

Function for generating combined phylogenetic FASTA datasets. 
"""

# Imports
import csv
import logging
import re
from pathlib import Path
from typing import Callable, TextIO

from Bio import Entrez, SeqIO
from Bio.SeqRecord import SeqRecord

def parse_top_blast_hits(
        top_hits_path: str | Path,
        logger: logging.Logger | None = None
) -> list[dict]:
    """Parse selected BLAST hits from a TSV file.
    
    Args:
        top_hits_path (str | Path): Path to TSV file containing BLAST hits.
        logger (logging.Logger, optional): Logger for logging messages. Defaults to None.
    
    Returns:
        list[dict]: List of dictionaries containing BLAST hits.
    
    Raises:
        FileNotFoundError: If the TSV file does not exist.
        ValueError: If the TSV file is not a file.
    """
    # Normalizing path.
    top_hits_path = Path(top_hits_path)

    # Verifying path.
    if not top_hits_path.exists():
        if logger is not None: logger.error(f"Top BLAST-hit file not found: {top_hits_path}")
        raise FileNotFoundError(f"Top BLAST-hit file not found: {top_hits_path}")
    if not top_hits_path.is_file():
        if logger is not None: logger.error(f"Top BLAST-hit file is not a file: {top_hits_path}")
        raise ValueError(f"Top BLAST-hit file is not a file: {top_hits_path}")
    
    # Parsing TSV.
    with top_hits_path.open("r", encoding = "utf-8", newline = "") as handle:
        reader = csv.DictReader(handle, delimiter = "\t")

        # Raising error if fieldnames is empty.
        if reader.fieldnames is None:
            if logger is not None: logger.error(f"Top BLAST-hit file is empty: {top_hits_path}")
            raise ValueError(f"Top BLAST-hit file is empty: {top_hits_path}")

        # Specifying required columns.
        required_columns = {
            "rank", "sseqid", "sscinames",
        }

        # Extracting missing columns (if any).
        missing_columns = required_columns.difference(reader.fieldnames)

        # Raising error if missing columns.
        if missing_columns:
            missing_text = ",".join(sorted(missing_columns))
            if logger is not None: logger.error(f"Top BLAST-hit file is missing required columns: {missing_text}")
            raise ValueError(f"Top BLAST-hit file is missing required columns: {missing_text}")
        
        # Initializing empty matches list.
        matches = []

        # Parsing TSV and appending to matches list.
        for line_number, row in enumerate(reader, start = 2,):
            if not row or all(str(value).strip() == "" for value in row.values()): continue
            try:
                row["rank"] = int(row["rank"])
            except (TypeError, ValueError) as error:
                if logger is not None: logger.error(f"Invalid rank on line {line_number} of {top_hits_path}: {row.get('rank')}")
                raise ValueError(f"Invalid rank on line {line_number} of {top_hits_path}: {row.get('rank')}") from error
            matches.append(row)
        
    # Verifying matches.
    if not matches:
        if logger is not None: logger.error(f"No selected BLAST hits found in {top_hits_path}")
        raise ValueError(f"No selected BLAST hits found in {top_hits_path}")
    
    # Ordering matches by rank.
    matches.sort(key = lambda match: match["rank"])

    # Logging.
    if logger is not None: logger.info(f"Parsed {len(matches)} selected BLAST hits from {top_hits_path}.")

    # Returning matches.
    return matches
    
def normalize_blast_accession(
        subject_id: str,
        logger: logging.Logger | None = None,
) -> str:
    """Extract an accession from a BLAST subject identifier.

    Examples:
        NC_012345.1 -> NC_012345.1
        ref|NC_012345.1| -> NC_012345.1
        gb|MW123456.1| -> MW123456.1

    Args:
        subject_id (str): BLAST subject identifier.
        logger (logging.Logger | None, optional): Logger for
            logging messages. Defaults to None.

    Returns:
        str: Normalized BLAST accession.

    Raises:
        ValueError: If no accession can be extracted.
    """
    # Normalizing subject identifier.
    subject_id = subject_id.strip()

    if not subject_id:
        if logger is not None:
            logger.error(
                "BLAST subject identifier cannot be empty."
            )

        raise ValueError(
            "BLAST subject identifier cannot be empty."
        )

    # Splitting pipe-delimited identifiers.
    parts = [
        part.strip()
        for part in subject_id.split("|")
        if part.strip()
    ]

    database_prefixes = {
        "ref",
        "gb",
        "emb",
        "dbj",
        "tpg",
        "tpe",
        "tpd",
    }

    # Extracting accession.
    if (
        len(parts) >= 2
        and parts[0].lower() in database_prefixes
    ):
        accession = parts[1]
    else:
        accession = parts[0]

    # Verifying accession.
    if not accession:
        if logger is not None:
            logger.error(
                "Could not extract accession from BLAST subject "
                f"identifier: {subject_id}."
            )

        raise ValueError(
            "Could not extract accession from BLAST subject "
            f"identifier: {subject_id}."
        )

    return accession

def standardize_sequence_name(value: str) -> str:
    """Standardize text for use in a FASTA identifier.
    
    Args:
        value (str): Text to standardize.

    Returns:
        str: Standardized text.
    """
    # Removing leading and trailing whitespace.
    value = value.strip()

    # Replacing whitespace with underscores.
    value = re.sub(r"\s+", "_", value,)

    # Removing characters unsuitable for identifiers.
    value = re.sub(r"[^a-zA-Z0-9_.-]", "_", value)

    # Collapsing repeated underscores.
    value = re.sub(r"_+", "_", value)

    # Removing surrounding underscores.
    value = value.strip("_")

    # Returning value. 
    if not value: return "unknown"
    return value

def build_assembled_sequence_name(sample_id: str) -> str:
    """Build the standardized assembled-genome identifier.

    Args:
        sample_id (str): Pipeline sample identifier.
    
    Returns:
        str: Standardized assembled-genome identifier.
    """
    return (
        f"{standardize_sequence_name(sample_id)}"
        "|assembled"
    )

def build_reference_sequence_name(
        rank: int,
        accession: str,
        scientific_name: str,
) -> str:
    """Build a standardized reference-sequence identifier.

    Args:
        rank (int): BLAST-match rank.
        accession (str): Sequence accession.
        scientific_name (str): Scientific name.

    Returns:
        str: Standardized reference-sequence identifier.
    """
    standardized_accession = standardize_sequence_name(
        accession
    )

    standardized_name = standardize_sequence_name(
        scientific_name
    )

    return (
        f"reference_{rank:02d}"
        f"|{standardized_accession}"
        f"|{standardized_name}"
    )


def read_assembled_genome(
        assembly_fasta: str | Path,
        sample_id: str,
        logger: logging.Logger | None = None,
) -> SeqRecord:
    """Read and standardize one assembled mitochondrial genome.

    Args:
        assembly_fasta (str | Path): Path to assembled-genome FASTA.
        sample_id (str): Pipeline sample identifier.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.

    Returns:
        SeqRecord: Standardized assembled-genome record.

    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the FASTA does not contain exactly one
            non-empty sequence.
    """
    # Normalizing path.
    assembly_fasta = Path(assembly_fasta)

    # Verifying path.
    if not assembly_fasta.exists():
        if logger is not None:
            logger.error(
                f"Assembly FASTA not found: {assembly_fasta}."
            )

        raise FileNotFoundError(
            f"Assembly FASTA not found: {assembly_fasta}."
        )

    if not assembly_fasta.is_file():
        raise ValueError(
            f"Assembly FASTA path is not a file: "
            f"{assembly_fasta}."
        )

    # Reading records.
    records = list(
        SeqIO.parse(
            assembly_fasta,
            "fasta",
        )
    )

    # Validating record count.
    if not records:
        raise ValueError(
            f"No sequences found in assembly FASTA: "
            f"{assembly_fasta}."
        )

    if len(records) != 1:
        raise ValueError(
            "Expected exactly one assembled mitochondrial "
            f"sequence in {assembly_fasta}, but found "
            f"{len(records)}."
        )

    record = records[0]

    # Validating sequence.
    if len(record.seq) == 0:
        raise ValueError(
            f"Assembly sequence is empty: {assembly_fasta}."
        )

    # Standardizing record.
    record.id = build_assembled_sequence_name(
        sample_id
    )
    record.name = record.id
    record.description = ""

    if logger is not None:
        logger.info(
            f"Read assembled genome containing "
            f"{len(record.seq)} bases from {assembly_fasta}."
        )

    return record


def retrieve_reference_sequences(
        accessions: list[str],
        entrez_email: str,
        entrez_api_key: str | None = None,
        logger: logging.Logger | None = None,
        efetch: Callable[..., TextIO] | None = None,
) -> list[SeqRecord]:
    """Retrieve nucleotide sequences from NCBI.

    Args:
        accessions (list[str]): Nucleotide accessions to retrieve.
        entrez_email (str): Email used for NCBI Entrez requests.
        entrez_api_key (str | None, optional): NCBI API key.
            Defaults to None.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.
        efetch (Callable[..., TextIO] | None, optional): Alternate
            Entrez fetch function for testing. Defaults to None.

    Returns:
        list[SeqRecord]: Retrieved nucleotide records.

    Raises:
        ValueError: If accessions or Entrez email are empty.
    """
    # Validating arguments.
    if not accessions:
        raise ValueError(
            "At least one accession is required."
        )

    if not entrez_email.strip():
        raise ValueError(
            "An Entrez email address is required."
        )

    # Configuring Entrez.
    Entrez.email = entrez_email.strip()

    if entrez_api_key:
        Entrez.api_key = entrez_api_key.strip()
    else:
        Entrez.api_key = None

    if efetch is None:
        efetch = Entrez.efetch

    if logger is not None:
        logger.info(
            f"Retrieving {len(accessions)} reference sequences "
            f"from NCBI."
        )

    # Retrieving sequences.
    with efetch(
            db="nucleotide",
            id=",".join(accessions),
            rettype="fasta",
            retmode="text",
    ) as handle:
        records = list(
            SeqIO.parse(
                handle,
                "fasta",
            )
        )

    if logger is not None:
        logger.info(
            f"Retrieved {len(records)} reference sequences "
            f"from NCBI."
        )

    return records


def order_and_standardize_reference_sequences(
        matches: list[dict],
        retrieved_records: list[SeqRecord],
        logger: logging.Logger | None = None,
) -> list[SeqRecord]:
    """Order retrieved records by BLAST rank and rename them.

    Args:
        matches (list[dict]): Selected BLAST matches.
        retrieved_records (list[SeqRecord]): Retrieved references.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.

    Returns:
        list[SeqRecord]: Ordered and standardized reference records.

    Raises:
        ValueError: If an expected accession was not retrieved.
    """
    # Indexing retrieved records.
    records_by_accession = {}

    for record in retrieved_records:
        full_accession = record.id
        accession_without_version = full_accession.split(".")[0]

        records_by_accession[full_accession] = record
        records_by_accession[accession_without_version] = record

    ordered_records = []

    # Ordering records using BLAST ranks.
    for match in matches:
        accession = normalize_blast_accession(
            match["sseqid"]
        )

        accession_without_version = accession.split(".")[0]

        record = records_by_accession.get(
            accession
        )

        if record is None:
            record = records_by_accession.get(
                accession_without_version
            )

        if record is None:
            raise ValueError(
                "NCBI did not return the expected reference "
                f"sequence: {accession}."
            )

        # Copying record before modifying identifiers.
        record = record[:]

        scientific_name = (
            match.get("sscinames")
            or "unknown_species"
        )

        record.id = build_reference_sequence_name(
            rank=match["rank"],
            accession=accession,
            scientific_name=scientific_name,
        )
        record.name = record.id
        record.description = ""

        if len(record.seq) == 0:
            raise ValueError(
                f"Retrieved reference sequence is empty: "
                f"{accession}."
            )

        ordered_records.append(record)

    if logger is not None:
        logger.info(
            f"Ordered and standardized "
            f"{len(ordered_records)} reference sequences."
        )

    return ordered_records


def validate_alignment_dataset(
        records: list[SeqRecord],
        expected_reference_count: int,
) -> None:
    """Validate records before writing the combined FASTA.

    Args:
        records (list[SeqRecord]): Combined sequence records.
        expected_reference_count (int): Expected number of
            references.

    Raises:
        ValueError: If records are missing, empty, duplicated, or
            incorrectly ordered.
    """
    expected_total = expected_reference_count + 1

    if len(records) != expected_total:
        raise ValueError(
            f"Expected {expected_total} total sequences but found "
            f"{len(records)}."
        )

    if not records[0].id.endswith("|assembled"):
        raise ValueError(
            "The assembled genome must be the first record."
        )

    identifiers = [
        record.id
        for record in records
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            "Duplicate sequence identifiers were generated."
        )

    for record in records:
        if len(record.seq) == 0:
            raise ValueError(
                f"Sequence is empty: {record.id}."
            )


def generate_alignment_dataset(
        sample_id: str,
        assembly_fasta: str | Path,
        top_hits_tsv: str | Path,
        output_fasta: str | Path,
        entrez_email: str,
        entrez_api_key: str | None = None,
        logger: logging.Logger | None = None,
        retrieve_function: Callable[..., list[SeqRecord]] | None = None,
) -> None:
    """Generate a combined unaligned phylogenetic FASTA dataset.

    Args:
        sample_id (str): Pipeline sample identifier.
        assembly_fasta (str | Path): Assembled-genome FASTA.
        top_hits_tsv (str | Path): Selected BLAST-hit TSV.
        output_fasta (str | Path): Combined FASTA output path.
        entrez_email (str): Email used for NCBI retrieval.
        entrez_api_key (str | None, optional): NCBI API key.
            Defaults to None.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.
        retrieve_function (Callable | None, optional): Alternate
            retrieval function for tests. Defaults to None.
    """
    # Normalizing output path.
    output_fasta = Path(output_fasta)

    if retrieve_function is None:
        retrieve_function = retrieve_reference_sequences

    if logger is not None:
        logger.info(
            f"Generating alignment dataset for sample "
            f"{sample_id}."
        )

    # Reading assembly.
    assembly_record = read_assembled_genome(
        assembly_fasta=assembly_fasta,
        sample_id=sample_id,
        logger=logger,
    )

    # Reading selected BLAST matches.
    matches = parse_top_blast_hits(
        top_hits_path=top_hits_tsv,
        logger=logger,
    )

    # Extracting accessions.
    accessions = [
        normalize_blast_accession(
            match["sseqid"]
        )
        for match in matches
    ]

    # Retrieving reference sequences.
    retrieved_records = retrieve_function(
        accessions=accessions,
        entrez_email=entrez_email,
        entrez_api_key=entrez_api_key,
        logger=logger,
    )

    # Ordering and standardizing references.
    reference_records = (
        order_and_standardize_reference_sequences(
            matches=matches,
            retrieved_records=retrieved_records,
            logger=logger,
        )
    )

    # Combining records.
    combined_records = [
        assembly_record,
        *reference_records,
    ]

    # Validating output records.
    validate_alignment_dataset(
        records=combined_records,
        expected_reference_count=len(matches),
    )

    # Creating output directory.
    output_fasta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Writing combined FASTA.
    SeqIO.write(
        combined_records,
        output_fasta,
        "fasta",
    )

    if logger is not None:
        logger.info(
            f"Wrote {len(combined_records)} sequences to "
            f"{output_fasta}."
        )