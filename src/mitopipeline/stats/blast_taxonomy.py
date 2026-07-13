"""Resolve missing BLAST scientific names from titles or NCBI Entrez."""

from __future__ import annotations

import logging
import re
from typing import Callable, TextIO

from Bio import Entrez, SeqIO


MISSING_SCIENTIFIC_NAMES = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
    "unknown_species",
    "not available",
}


def normalize_blast_accession(subject_id: str) -> str:
    """Extract a nucleotide accession from a BLAST subject identifier."""
    value = str(subject_id).strip()
    if not value:
        raise ValueError("BLAST subject identifier cannot be empty.")

    parts = [part.strip() for part in value.split("|") if part.strip()]
    prefixes = {"ref", "gb", "emb", "dbj", "tpg", "tpe", "tpd"}

    if len(parts) >= 2 and parts[0].lower() in prefixes:
        return parts[1]

    return parts[0]


def scientific_name_is_missing(value: object) -> bool:
    """Return whether a scientific-name value is a placeholder."""
    return str(value or "").strip().lower() in MISSING_SCIENTIFIC_NAMES


def infer_scientific_name_from_title(title: object) -> str | None:
    """Infer a binomial scientific name from an NCBI-style title."""
    value = str(title or "").strip()
    if not value or value.lower() in MISSING_SCIENTIFIC_NAMES:
        return None

    # Remove a leading accession or database identifier when present.
    value = re.sub(
        r"^(?:ref|gb|emb|dbj)\|[^|]+\|\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"^[A-Z]{1,4}_?\d+(?:\.\d+)?\s+", "", value)

    match = re.match(
        r"^([A-Z][A-Za-z.-]+)\s+([a-z][A-Za-z.-]+)(?:\s+([a-z][A-Za-z.-]+))?",
        value,
    )
    if match is None:
        return None

    genus, species, third = match.groups()
    name = f"{genus} {species}"

    # Keep a third lowercase taxon only when it appears before common
    # record-description words.
    if third and third.lower() not in {
        "mitochondrion",
        "mitochondrial",
        "complete",
        "genome",
        "dna",
        "isolate",
        "voucher",
        "strain",
    }:
        name = f"{name} {third}"

    return name


def fetch_scientific_names(
    accessions: list[str],
    entrez_email: str,
    entrez_api_key: str | None = None,
    logger: logging.Logger | None = None,
    efetch: Callable[..., TextIO] | None = None,
) -> dict[str, str]:
    """Fetch organism names for nucleotide accessions from NCBI."""
    unique_accessions = list(dict.fromkeys(accessions))
    if not unique_accessions:
        return {}

    email = entrez_email.strip()
    if not email:
        raise ValueError(
            "An Entrez email is required to resolve missing BLAST taxonomy."
        )

    Entrez.email = email
    Entrez.api_key = entrez_api_key.strip() if entrez_api_key else None
    fetcher = efetch or Entrez.efetch

    if logger is not None:
        logger.info(
            "Resolving scientific names for %d NCBI accessions.",
            len(unique_accessions),
        )

    names: dict[str, str] = {}
    with fetcher(
        db="nucleotide",
        id=",".join(unique_accessions),
        rettype="gb",
        retmode="text",
    ) as handle:
        for record in SeqIO.parse(handle, "genbank"):
            organism = str(record.annotations.get("organism", "")).strip()
            if scientific_name_is_missing(organism):
                continue

            full_accession = record.id
            names[full_accession] = organism
            names[full_accession.split(".")[0]] = organism

            for accession in record.annotations.get("accessions", []):
                accession = str(accession).strip()
                if accession:
                    names[accession] = organism
                    names[accession.split(".")[0]] = organism

    return names


def enrich_blast_scientific_names(
    matches: list[dict],
    entrez_email: str,
    entrez_api_key: str | None = None,
    logger: logging.Logger | None = None,
    fetch_function: Callable[..., dict[str, str]] | None = None,
) -> list[dict]:
    """Normalize accessions and fill missing BLAST scientific names."""
    enriched = [dict(match) for match in matches]
    unresolved: list[str] = []

    for match in enriched:
        accession = normalize_blast_accession(match.get("sseqid", ""))
        match["sseqid"] = accession

        if not scientific_name_is_missing(match.get("sscinames")):
            continue

        title_name = infer_scientific_name_from_title(match.get("stitle"))
        if title_name is not None:
            match["sscinames"] = title_name
        else:
            unresolved.append(accession)

    if unresolved:
        resolver = fetch_function or fetch_scientific_names
        resolved = resolver(
            accessions=unresolved,
            entrez_email=entrez_email,
            entrez_api_key=entrez_api_key,
            logger=logger,
        )

        for match in enriched:
            if not scientific_name_is_missing(match.get("sscinames")):
                continue

            accession = match["sseqid"]
            scientific_name = (
                resolved.get(accession)
                or resolved.get(accession.split(".")[0])
            )
            match["sscinames"] = scientific_name or "unknown_species"

    return enriched
