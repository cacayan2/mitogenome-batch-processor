"""Assess and select mitochondrial contigs from a GetOrganelle assembly."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Iterable

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


@dataclass(frozen=True)
class ContigEvidence:
    """Aggregated BLAST evidence for one assembly contig."""

    contig_id: str
    length: int
    hit_count: int
    best_bitscore: float
    best_identity: float | None
    best_query_coverage: float | None


@dataclass(frozen=True)
class AssemblyAssessment:
    """Machine-readable assessment of a mitochondrial assembly."""

    status: str
    primary_contig_id: str
    primary_contig_length: int
    assembly_contig_count: int
    mitochondrial_contig_count: int
    mitochondrial_total_length: int
    complete_min_length: int
    complete_max_length: int
    circular_visualization_allowed: bool
    reason: str
    mitochondrial_contigs: tuple[ContigEvidence, ...]

    def to_dict(self) -> dict:
        result = asdict(self)
        result["mitochondrial_contigs"] = [
            asdict(item) for item in self.mitochondrial_contigs
        ]
        return result


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_records(assembly_fasta: str | Path) -> dict[str, SeqRecord]:
    path = Path(assembly_fasta)
    if not path.is_file():
        raise FileNotFoundError(f"Assembly FASTA file not found: {path}")

    records = {record.id: record for record in SeqIO.parse(path, "fasta")}
    if not records:
        raise ValueError(f"Assembly FASTA contains no records: {path}")
    return records


def _read_hit_rows(top_hits_tsv: str | Path) -> list[dict[str, str]]:
    path = Path(top_hits_tsv)
    if not path.is_file():
        raise FileNotFoundError(f"Top-hit TSV file not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"Top-hit TSV is empty: {path}")
        if "qseqid" not in reader.fieldnames:
            raise ValueError(f"Top-hit TSV is missing qseqid: {path}")
        rows = [row for row in reader if row.get("qseqid", "").strip()]

    if not rows:
        raise ValueError(f"No BLAST query IDs were found in {path}")
    return rows


def read_blast_query_ids(top_hits_tsv: str | Path) -> set[str]:
    """Read unique assembly-contig IDs represented by selected BLAST hits."""
    return {row["qseqid"].strip() for row in _read_hit_rows(top_hits_tsv)}


def _evidence_for_hits(
    records: dict[str, SeqRecord],
    hit_rows: Iterable[dict[str, str]],
    minimum_fragment_length: int,
) -> tuple[ContigEvidence, ...]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in hit_rows:
        grouped[row["qseqid"].strip()].append(row)

    evidence: list[ContigEvidence] = []
    missing = sorted(set(grouped) - set(records))
    if missing:
        raise ValueError(
            "BLAST hits refer to contigs absent from the assembly FASTA: "
            f"{missing}"
        )

    for contig_id, rows in grouped.items():
        length = len(records[contig_id].seq)
        if length < minimum_fragment_length:
            continue

        bitscores = [
            value
            for value in (_optional_float(row.get("bitscore")) for row in rows)
            if value is not None
        ]
        identities = [
            value
            for value in (_optional_float(row.get("pident")) for row in rows)
            if value is not None
        ]
        coverages = [
            value
            for value in (
                _optional_float(row.get("qcovs") or row.get("qcovhsp"))
                for row in rows
            )
            if value is not None
        ]

        evidence.append(
            ContigEvidence(
                contig_id=contig_id,
                length=length,
                hit_count=len(rows),
                best_bitscore=max(bitscores, default=0.0),
                best_identity=max(identities) if identities else None,
                best_query_coverage=max(coverages) if coverages else None,
            )
        )

    if not evidence:
        raise ValueError(
            "No BLAST-supported contigs passed the minimum fragment length "
            f"of {minimum_fragment_length} bases."
        )

    return tuple(
        sorted(
            evidence,
            key=lambda item: (
                item.best_bitscore,
                item.best_query_coverage or 0.0,
                item.length,
                item.contig_id,
            ),
            reverse=True,
        )
    )


def assess_mitochondrial_assembly(
    assembly_fasta: str | Path,
    top_hits_tsv: str | Path,
    *,
    complete_min_length: int = 14_000,
    complete_max_length: int = 22_000,
    minimum_fragment_length: int = 200,
) -> tuple[AssemblyAssessment, SeqRecord, list[SeqRecord]]:
    """Classify an assembly and return its primary and supported records.

    This function deliberately does not concatenate scaffolds. Multiple
    BLAST-supported scaffolds are preserved as fragments and classified as a
    fragmented assembly unless one primary contig independently satisfies the
    configured completeness-length interval.
    """
    if complete_min_length <= 0:
        raise ValueError("complete_min_length must be greater than zero")
    if complete_max_length < complete_min_length:
        raise ValueError("complete_max_length must be >= complete_min_length")
    if minimum_fragment_length <= 0:
        raise ValueError("minimum_fragment_length must be greater than zero")

    records = _load_records(assembly_fasta)
    evidence = _evidence_for_hits(
        records,
        _read_hit_rows(top_hits_tsv),
        minimum_fragment_length,
    )

    primary_evidence = evidence[0]
    primary = records[primary_evidence.contig_id]
    mitochondrial_records = [records[item.contig_id] for item in evidence]
    mitochondrial_total_length = sum(item.length for item in evidence)

    primary_complete_length = (
        complete_min_length
        <= primary_evidence.length
        <= complete_max_length
    )

    if primary_complete_length:
        status = "complete_candidate"
        circular_allowed = True
        if len(evidence) == 1:
            reason = (
                "One BLAST-supported contig falls within the configured "
                "complete mitogenome length interval."
            )
        else:
            reason = (
                "The primary BLAST-supported contig falls within the complete "
                "length interval; additional mitochondrial-like scaffolds were "
                "retained."
            )
    elif len(evidence) > 1:
        status = "fragmented"
        circular_allowed = False
        reason = (
            "Multiple BLAST-supported mitochondrial scaffolds were detected "
            "and no single scaffold satisfied the configured complete-length "
            "interval. Scaffolds were preserved without concatenation."
        )
    else:
        status = "partial"
        circular_allowed = False
        reason = (
            "The only BLAST-supported mitochondrial scaffold did not satisfy "
            "the configured complete mitogenome length interval."
        )

    assessment = AssemblyAssessment(
        status=status,
        primary_contig_id=primary.id,
        primary_contig_length=len(primary.seq),
        assembly_contig_count=len(records),
        mitochondrial_contig_count=len(evidence),
        mitochondrial_total_length=mitochondrial_total_length,
        complete_min_length=complete_min_length,
        complete_max_length=complete_max_length,
        circular_visualization_allowed=circular_allowed,
        reason=reason,
        mitochondrial_contigs=evidence,
    )
    return assessment, primary, mitochondrial_records


def write_assessment(
    assessment: AssemblyAssessment,
    output_json: str | Path,
) -> None:
    path = Path(output_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(assessment.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def select_mitochondrial_contig(
    assembly_fasta: str | Path,
    top_hits_tsv: str | Path,
    output_fasta: str | Path,
) -> SeqRecord:
    """Backward-compatible primary-contig selection helper.

    New pipeline code should call :func:`assess_mitochondrial_assembly` so that
    fragmented assemblies are not silently treated as complete genomes.
    """
    _, primary, _ = assess_mitochondrial_assembly(
        assembly_fasta,
        top_hits_tsv,
        complete_min_length=1,
        complete_max_length=10**12,
    )
    path = Path(output_fasta)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = SeqIO.write([primary], path, "fasta")
    if written != 1:
        raise RuntimeError(f"Expected to write one sequence but wrote {written}")
    return primary
