"""report_stats.py

Collect and normalize statistics used in per-sample Markdown reports. 
"""

# Imports
import csv
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any
from Bio import SeqIO

def read_sample_meta_data(runtime_manifest_path: str | Path, sample_id: str, logger: logging.Logger | None = None) -> dict[str, str]:
    """Read metadata for one sample from the runtime manifest.
    
    Args: 
        runtime_manifest_path (str | Path): Runtime manifest path.
        sample_id (str): Sample identifier.
        logger (logging.logger | None, optional): Logger to use. Defaults to None.
        
    Returns:
        dict[str, str]: Sample metadata.
    
    Raises:
        FileNotFoundError: If the runtime manifest does not exist.
        ValueError: If the sample cannot be found.
    """
    # Normalizing the runtime manifest path. 
    runtime_manifest_path = Path(runtime_manifest_path)

    # Validating that the runtime_manifest_path exists.
    if not runtime_manifest_path.exists():
        if logger is not None: logger.error(f"Runtime manifest does not exist: {runtime_manifest_path}")
        raise FileNotFoundError(f"Runtime manifest does not exist: {runtime_manifest_path}")

    # Reading the runtime manifest.
    with open(runtime_manifest_path, "r", encoding = "utf-8", newline = "") as handle:
        reader = csv.DictReader(handle, delimiter = "\t")
        
        # Iterating through the manifest and obtaining the sample metadata.
        for row in reader:
            if row.get("sample_id", "").strip() == sample_id:
                metadata = {
                    key: value.strip() for key, value in row.items()
                    if key is not None and value is not None and value.strip()
                }
                if logger is not None:
                    logger.info(f"Successfully loaded metadata for sample {sample_id}.")
                return metadata
        
        if logger is not None: logger.error(f"Sample {sample_id} not found in runtime manifest.")
        raise ValueError(f"Sample {sample_id} not found in runtime manifest.")

def parse_fastp_report(json_path: str | Path, logger: logging.Logger | None = None,) -> dict[str, Any] | None:
    """Parse a fastp JSON report when available.

    Args:
        json_path (str | Path): Path to the fastp JSON report.
        logger (logging.Logger | None, optional): Logger to use. Defaults to None.

    Returns:
        dict[str, Any] | None: Parsed report.
    """
    # Normalizing path.
    json_path = Path(json_path)

    # Verification of json_path.
    if not json_path.exists():
        if logger is not None: logger.error(f"Fastp json file not found: {json_path}")
        return None

    # Loading the json file.
    with open(json_path, "r", encoding = "utf-8") as handle:
        data = json.load(handle)
        if logger is not None: logger.info(f"Fastp json file loaded: {json_path}")
        
        # Extracting before and after statistics. 
        before = data["summary"]["before_filtering"]
        after = data["summary"]["after_filtering"]
        filtering = data.get("filtering_result", {})
        adapter = data.get("adapter_cutting", {})
        reads_in = int(before["total_reads"])
        reads_out = int(after["total_reads"])
        bases_in = int(before["total_bases"])
        bases_out = int(after["total_bases"])

        # Creating result dictionary.
        result = {
            "reads_in": reads_in,
            "reads_out": reads_out,
            "reads_removed": reads_in - reads_out,
            "read_retention_rate": (reads_out / reads_in if reads_in > 0 else 0),
            "bases_in": bases_in,
            "bases_out": bases_out,
            "bases_removed": bases_in - bases_out,
            "base_retention_rate": (bases_out / bases_in if bases_in > 0 else 0),
            "q20_rate_in": before["q20_rate"],
            "q20_rate_out": after["q20_rate"],
            "q30_rate_in": before["q30_rate"],
            "q30_rate_out": after["q30_rate"],
            "gc_content_in": before["gc_content"],
            "gc_content_out": after["gc_content"],
            "reads_passing_filtering": int(filtering.get("passed_filter_reads", reads_out)),
            "low_quality_reads": int(filtering.get("low_quality_reads", 0)),
            "too_many_n_reads": int(filtering.get("too_many_n_reads", 0)),
            "too_short_reads": int(filtering.get("too_short_reads", 0)),
            "too_long_reads": int(filtering.get("too_long_reads", 0)),
            "adapter_trimmed_reads": int(adapter.get("adapter_trimmed_reads", 0)),
            "adapter_trimmed_bases": int(adapter.get("adapter_trimmed_bases", 0)),
        }

    # Logging and returning dictionary.
    if logger is not None: logger.info(f"Fastp json file parsed: {json_path}")
    return result
        
def calculate_gc_percent(sequence: str,) -> float:
    """Calculate GC percentage from an assembled sequence.
    
    Args:
        sequence (str): Assembled sequence.
    
    Returns:
        float: GC percentage.
    """
    # Obtaining valid bases.
    valid_bases = [base for base in sequence.upper if base in {"A", "C", "G", "T"}]
    
    # Returning 0 if bases is empty.
    if not valid_bases: return 0.0

    # Obtaining number of GC bases.
    gc_bases = sum(base in {"G", "C"} for base in valid_bases)

    # Returning GC percentage.
    return (gc_bases / len(valid_bases)) * 100

def parse_assembly_report(fasta_path: str | Path, logger: logging.Logger | None = None,) -> dict[str, Any] | None:
    """Calculate assembly statistics when an assembly exists.
    
    Args:
        fasta_path (str | Path): Path to the assembly FASTA file.
        logger (logging.Logger | None, optional): Logger to use. Defaults to None.
    
    Returns: 
        dict[str, Any] | None: Assembly statistics.
    """
    # Normalizing path.
    fasta_path = Path(fasta_path)

    # Validating fasta.
    if not fasta_path.exists():
        if logger is not None: logger.error(f"Assembly FASTA not found: {fasta_path}")
        return None
    
    # Parsing with SeqIO.
    records = list(SeqIO.parse(fasta_path, "fasta"))

    # Verification of records.
    if not records:
        if logger is not None: logger.error(f"Assembly FASTA is empty: {fasta_path}")
        raise ValueError(f"Assembly FASTA is empty: {fasta_path}")
    
    # Obtaining lengths of sequences.
    lengths = [len(record.seq) for record in records]

    # Joining length of all sequences in assembly.
    combined_sequence = "".join(record.seq for record in records)

    # Obtaining ambiguous bases.
    ambiguous_bases = sum(base.upper() not in {"A", "C", "G", "T"} for base in combined_sequence)

    # Creating result dictionary.
    result = {
        "contig_count": len(records),
        "total_length_bp": sum(lengths),
        "longest_contig_bp": max(lengths),
        "shortest_contig_bp": min(lengths),
        "gc_content_percent": calculate_gc_percent(combined_sequence)
    }

    # Logging and returning dictionary.
    if logger is not None: logger.info(f"Calculated assembly statistics from: {fasta_path}")
    return result

def parse_gff_attributes(attributes_text: str, logger: logging.Logger | None = None,) -> dict[str, str] | None:
    """Parse GFF attributes into a dictionary.
    
    Args:
        attributes_text (str): Attributes text.
        logger (logging.Logger | None, optional): Logger to use. Defaults to None.
    
    Returns:
        dict[str, str]: Dictionary of attributes.
    """
    # Initializing dictionary.
    attributes: dict[str, str] = {}

    # Parsing attributes.
    for item in attributes_text.split(";"):
        item = item.strip()
        if not item: continue
        if "=" in item:
            key, value = item.split("=", maxsplit = 1,)
            attributes[key.strip()] = value.strip()
    
    # Logging and returning dictionary.
    if logger is not None: logger.info(f"Parsed GFF attributes: {attributes_text}")
    return attributes

def discover_annotation_gff(annotation_directory: str | Path, logger: logging.Logger | None = None) -> Path | None:
    """Find the primary GFF/GFF#3 annotation output.
    
    Args:
        annotation_directory (str| Path): Per-sample annotation directory.
    
    Returns:
        Path | None: Selected annotation file.
    """
    # Normalizing path.
    annotation_directory = Path(annotation_directory)

    # Validating directory.
    if not annotation_directory.exists():
        if logger is not None: logger.error(f"Annotation directory not found: {annotation_directory}")
        return None
    
    # Obtaining candidate GFF files.
    candidates = sorted([*annotation_directory.rglob("*.gff"),
                         *annotation_directory.rglob("*.gff3"),],
    key = lambda path: path(path.name.lower() not in {"result.gff", "result.gff3",}, len(path.parts), path.name,))

    # Validating candidates.
    if not candidates: return None

    # Logging and returning path.
    if logger is not None: logger.info(f"Discovered annotation GFF: {candidates[0]}")
    return candidates[0]

def parse_annotation_report(
        annotation_directory: str | Path,
        logger: logging.Logger | None = None,
) -> dict[str, Any] | None:
    """Summarize mitochondrial annotations from a GFF file.

    Args:
        annotation_directory (str | Path): MITOS2 sample output directory.
        logger (logging.Logger | None, optional): Logger. Defaults to None.

    Returns:
        dict[str, Any] | None: Annotation summary.
    """
    gff_path = discover_annotation_gff(
        annotation_directory
    )

    if gff_path is None:
        if logger is not None:
            logger.info(
                "Optional annotation GFF was not found under "
                f"{annotation_directory}."
            )

        return None

    feature_counts: Counter[str] = Counter()
    gene_names: list[str] = []

    with gff_path.open(
            "r",
            encoding="utf-8",
            errors="replace",
    ) as handle:
        for line_number, line in enumerate(
                handle,
                start=1,
        ):
            line = line.rstrip("\n")

            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            if len(fields) != 9:
                raise ValueError(
                    f"Invalid GFF row {line_number} in "
                    f"{gff_path}: expected 9 columns."
                )

            feature_type = fields[2].strip()

            feature_counts[
                feature_type
            ] += 1

            attributes = parse_gff_attributes(
                fields[8]
            )

            gene_name = (
                attributes.get("Name")
                or attributes.get("gene")
                or attributes.get("product")
                or attributes.get("ID")
            )

            if gene_name:
                gene_names.append(
                    gene_name
                )

    result = {
        "gff_path": str(
            gff_path.resolve()
        ),
        "total_features": sum(
            feature_counts.values()
        ),
        "feature_counts": dict(
            sorted(
                feature_counts.items()
            )
        ),
        "gene_names": sorted(
            set(gene_names)
        ),
    }

    if logger is not None:
        logger.info(
            f"Parsed annotation statistics from {gff_path}."
        )

    return result


def parse_blast_report(
        top_hits_path: str | Path,
        logger: logging.Logger | None = None,
) -> list[dict[str, Any]] | None:
    """Read ranked BLAST matches when available.

    Args:
        top_hits_path (str | Path): Ranked BLAST TSV.
        logger (logging.Logger | None, optional): Logger. Defaults to None.

    Returns:
        list[dict[str, Any]] | None: Ranked BLAST matches.
    """
    top_hits_path = Path(
        top_hits_path
    )

    if not top_hits_path.exists():
        if logger is not None:
            logger.info(
                f"Optional BLAST hits file not found: "
                f"{top_hits_path}."
            )

        return None

    with top_hits_path.open(
            "r",
            encoding="utf-8",
            errors="replace",
            newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        rows = list(reader)

    matches: list[dict[str, Any]] = []

    for row in rows:
        matches.append(
            {
                "rank": int(
                    row["rank"]
                ),
                "subject_id": row[
                    "sseqid"
                ],
                "scientific_name": row.get(
                    "sscinames",
                    "",
                ),
                "percent_identity": float(
                    row["pident"]
                ),
                "query_coverage": float(
                    row["qcovs"]
                ),
                "alignment_length": int(
                    row["length"]
                ),
                "evalue": float(
                    row["evalue"]
                ),
                "bitscore": float(
                    row["bitscore"]
                ),
                "title": row.get(
                    "stitle",
                    "",
                ),
            }
        )

    matches.sort(
        key=lambda match: match["rank"]
    )

    if logger is not None:
        logger.info(
            f"Parsed {len(matches)} ranked BLAST matches from "
            f"{top_hits_path}."
        )

    return matches


def collect_output_paths(
        job_directory: str | Path,
        sample_id: str,
) -> dict[str, Path]:
    """Construct known per-sample output paths."""
    job_directory = Path(
        job_directory
    )

    return {
        "runtime_manifest": (
            job_directory
            / "metadata"
            / "runtime_manifest.tsv"
        ),
        "fastp_json": (
            job_directory
            / "trimming"
            / f"{sample_id}.fastp.json"
        ),
        "fastp_html": (
            job_directory
            / "trimming"
            / f"{sample_id}.fastp.html"
        ),
        "assembly_fasta": (
            job_directory
            / "assembly"
            / f"{sample_id}.fasta"
        ),
        "annotation_directory": (
            job_directory
            / "annotation"
            / sample_id
        ),
        "blast_top_hits": (
            job_directory
            / "phylogeny"
            / "blast"
            / f"{sample_id}.top_hits.tsv"
        ),
        "alignment_fasta": (
            job_directory
            / "phylogeny"
            / "alignment"
            / f"{sample_id}.aligned.fasta"
        ),
        "newick_tree": (
            job_directory
            / "phylogeny"
            / "trees"
            / f"{sample_id}.maximum_likelihood.nwk"
        ),
        "tree_svg": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.svg"
        ),
        "tree_pdf": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.pdf"
        ),
        "tree_png": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.png"
        ),
        "phylogeny_summary": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.phylogeny.md"
        ),
    }