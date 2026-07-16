"""Automated rescue helpers for fragmented mitochondrial assemblies.

The implementation is conservative: every reconstruction is scored, all evidence
is retained, and a candidate is promoted only when it improves on the original.
Reference-guided drafts are never labeled as de novo circular assemblies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable
import csv
import json
import math
import re
import shutil
import subprocess

from Bio import Entrez, SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


@dataclass
class Candidate:
    name: str
    method: str
    fasta: str
    length: int
    contig_count: int
    circular: bool = False
    graph_unique_path: bool = False
    mean_depth: float | None = None
    covered_fraction: float | None = None
    reference_coverage: float | None = None
    reference_identity: float | None = None
    n_fraction: float = 0.0
    score: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def run(command: list[str], *, cwd: Path | None = None, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        stdout=stdout,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def load_records(path: str | Path) -> list[SeqRecord]:
    records = list(SeqIO.parse(Path(path), "fasta"))
    if not records:
        raise ValueError(f"No FASTA records found in {path}")
    return records


def fasta_metrics(path: str | Path) -> tuple[int, int, float]:
    records = load_records(path)
    sequence = "".join(str(record.seq).upper() for record in records)
    length = len(sequence)
    n_fraction = sequence.count("N") / length if length else 0.0
    return length, len(records), n_fraction


def terminal_overlap(record: SeqRecord, minimum: int, maximum: int, identity: float) -> int:
    sequence = str(record.seq).upper()
    maximum = min(maximum, len(sequence) // 2)
    for size in range(maximum, minimum - 1, -1):
        left = sequence[:size]
        right = sequence[-size:]
        matches = sum(a == b for a, b in zip(left, right))
        if matches / size >= identity:
            return size
    return 0


def circularize_terminal_overlap(
    input_fasta: Path,
    output_fasta: Path,
    minimum: int,
    maximum: int,
    identity: float,
) -> Candidate | None:
    records = load_records(input_fasta)
    if len(records) != 1:
        return None
    overlap = terminal_overlap(records[0], minimum, maximum, identity)
    if overlap == 0:
        return None
    record = records[0][:-overlap]
    record.id = f"{records[0].id}|terminal_overlap_circularized"
    record.description = f"terminal overlap removed: {overlap} bp"
    output_fasta.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write([record], output_fasta, "fasta")
    length, count, n_fraction = fasta_metrics(output_fasta)
    return Candidate(
        name="terminal_overlap",
        method="terminal_overlap",
        fasta=str(output_fasta),
        length=length,
        contig_count=count,
        circular=True,
        n_fraction=n_fraction,
        notes=[f"Removed a {overlap}-bp terminal overlap."],
    )


def parse_gfa_unique_path(gfa_path: Path, allowed_ids: set[str]) -> list[tuple[str, str]] | None:
    segments: dict[str, str] = {}
    adjacency: dict[str, list[tuple[str, str]]] = {}
    indegree: dict[str, int] = {}
    with gfa_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip().split("\t")
            if not fields:
                continue
            if fields[0] == "S" and len(fields) >= 3:
                segments[fields[1]] = fields[2]
            elif fields[0] == "L" and len(fields) >= 6:
                source, source_orient, target, target_orient = fields[1:5]
                if source in allowed_ids and target in allowed_ids:
                    adjacency.setdefault(source, []).append((target, target_orient))
                    indegree[target] = indegree.get(target, 0) + 1
                    indegree.setdefault(source, indegree.get(source, 0))
    nodes = allowed_ids & set(segments)
    if not nodes:
        return None
    if any(len(adjacency.get(node, [])) > 1 or indegree.get(node, 0) > 1 for node in nodes):
        return None
    starts = [node for node in nodes if indegree.get(node, 0) == 0]
    if len(starts) != 1:
        return None
    path: list[tuple[str, str]] = [(starts[0], "+")]
    seen = {starts[0]}
    current = starts[0]
    while adjacency.get(current):
        nxt, orient = adjacency[current][0]
        if nxt in seen:
            return None
        path.append((nxt, orient))
        seen.add(nxt)
        current = nxt
    return path if seen == nodes else None


def reconstruct_gfa_path(gfa_path: Path, fragments_fasta: Path, output_fasta: Path) -> Candidate | None:
    records = {record.id: record for record in load_records(fragments_fasta)}
    path = parse_gfa_unique_path(gfa_path, set(records))
    if path is None or len(path) < 2:
        return None
    pieces: list[str] = []
    for contig_id, orientation in path:
        seq = records[contig_id].seq
        pieces.append(str(seq if orientation == "+" else seq.reverse_complement()))
    record = SeqRecord(Seq("".join(pieces)), id="graph_resolved", description="unique GFA path")
    output_fasta.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write([record], output_fasta, "fasta")
    length, count, n_fraction = fasta_metrics(output_fasta)
    return Candidate(
        name="graph_resolved",
        method="gfa_unique_path",
        fasta=str(output_fasta),
        length=length,
        contig_count=count,
        graph_unique_path=True,
        n_fraction=n_fraction,
        notes=["Reconstructed from a unique nonbranching path in graph.gfa."],
    )


def map_reads(reference: Path, r1: Path, r2: Path, output_dir: Path, threads: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    bam = output_dir / "reads.bam"
    minimap = subprocess.Popen(
        ["minimap2", "-ax", "sr", "-t", str(threads), str(reference), str(r1), str(r2)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    sort = subprocess.run(
        ["samtools", "sort", "-@", str(max(1, threads // 2)), "-o", str(bam), "-"],
        stdin=minimap.stdout,
        stderr=subprocess.PIPE,
        check=False,
    )
    if minimap.stdout:
        minimap.stdout.close()
    minimap.wait()
    if minimap.returncode or sort.returncode:
        return {"available": False, "reason": "minimap2/samtools mapping failed"}
    run(["samtools", "index", str(bam)])
    coverage = run(["samtools", "coverage", str(bam)])
    depths: list[float] = []
    covered: list[float] = []
    if coverage.returncode == 0:
        for line in coverage.stdout.splitlines():
            if line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 7:
                covered.append(float(fields[5]) / 100.0)
                depths.append(float(fields[6]))
    return {
        "available": bool(depths),
        "bam": str(bam),
        "mean_depth": sum(depths) / len(depths) if depths else None,
        "covered_fraction": sum(covered) / len(covered) if covered else None,
    }


def first_reference_accession(top_hits: Path) -> str | None:
    with top_hits.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            value = (row.get("sseqid") or row.get("saccver") or "").strip()
            if value:
                return value.split("|")[-1]
    return None


def fetch_reference(top_hits: Path, email: str, api_key: str, output_fasta: Path) -> Path | None:
    accession = first_reference_accession(top_hits)
    if not accession or not email:
        return None
    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key
    try:
        with Entrez.efetch(db="nuccore", id=accession, rettype="fasta", retmode="text") as handle:
            text = handle.read()
        output_fasta.parent.mkdir(parents=True, exist_ok=True)
        output_fasta.write_text(text, encoding="utf-8")
        return output_fasta if output_fasta.stat().st_size else None
    except Exception:
        return None


def minimap_paf(reference: Path, query: Path, output: Path) -> list[list[str]]:
    with output.open("w", encoding="utf-8") as handle:
        completed = run(["minimap2", "-x", "asm5", str(reference), str(query)], stdout=handle)
    if completed.returncode != 0:
        return []
    rows = []
    for line in output.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 12:
            rows.append(fields)
    return rows


def reference_guided_draft(
    reference: Path,
    fragments: Path,
    output_fasta: Path,
    paf_path: Path,
    gap_n: int,
    maximum_gap: int,
) -> Candidate | None:
    records = {record.id: record for record in load_records(fragments)}
    rows = minimap_paf(reference, fragments, paf_path)
    best: dict[str, list[str]] = {}
    for row in rows:
        qname = row[0]
        matches = int(row[9])
        if qname not in best or matches > int(best[qname][9]):
            best[qname] = row
    if len(best) < 2:
        return None
    ordered = sorted(best.values(), key=lambda row: int(row[7]))
    sequence: list[str] = []
    previous_end: int | None = None
    aligned_bases = 0
    matches = 0
    for row in ordered:
        qname, strand = row[0], row[4]
        start, end = int(row[7]), int(row[8])
        seq = records[qname].seq
        if strand == "-":
            seq = seq.reverse_complement()
        if previous_end is not None:
            gap = max(0, min(maximum_gap, start - previous_end))
            sequence.append("N" * max(gap_n, gap))
        sequence.append(str(seq))
        previous_end = max(previous_end or 0, end)
        aligned_bases += int(row[10])
        matches += int(row[9])
    record = SeqRecord(Seq("".join(sequence)), id="reference_guided_draft", description="not de novo circular")
    output_fasta.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write([record], output_fasta, "fasta")
    reference_length = len(load_records(reference)[0].seq)
    length, count, n_fraction = fasta_metrics(output_fasta)
    return Candidate(
        name="reference_guided_draft",
        method="reference_guided_scaffolding",
        fasta=str(output_fasta),
        length=length,
        contig_count=count,
        reference_coverage=min(1.0, aligned_bases / reference_length) if reference_length else None,
        reference_identity=matches / aligned_bases if aligned_bases else None,
        n_fraction=n_fraction,
        notes=["Reference-guided draft with unresolved gaps represented by Ns; not de novo circular."],
    )


def discover_getorganelle_fasta(directory: Path) -> Path | None:
    patterns = ["*path_sequence.fasta", "*selected_graph*.fasta", "*.fasta"]
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(directory.rglob(pattern))
    candidates = [path for path in candidates if path.is_file() and path.stat().st_size > 0]
    return max(candidates, key=lambda path: path.stat().st_size) if candidates else None


def run_getorganelle_profile(
    name: str,
    profile: dict,
    r1: Path,
    r2: Path,
    output_dir: Path,
    organelle_type: str,
    threads: int,
) -> Candidate | None:
    profile_dir = output_dir / f"getorganelle_{name}"
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    command = [
        "get_organelle_from_reads.py", "-1", str(r1), "-2", str(r2),
        "-o", str(profile_dir), "-F", organelle_type, "-t", str(threads),
        "-R", str(profile.get("max_rounds", 10)),
    ]
    if profile.get("kmer"):
        command.extend(["-k", str(profile["kmer"])])
    if profile.get("target_coverage"):
        command.extend(["--reduce-reads-for-coverage", str(profile["target_coverage"])])
    completed = run(command)
    if completed.returncode != 0:
        return None
    fasta = discover_getorganelle_fasta(profile_dir)
    if fasta is None:
        return None
    normalized = profile_dir / "candidate.fasta"
    shutil.copy2(fasta, normalized)
    length, count, n_fraction = fasta_metrics(normalized)
    return Candidate(
        name=f"getorganelle_{name}",
        method="getorganelle_retry",
        fasta=str(normalized),
        length=length,
        contig_count=count,
        n_fraction=n_fraction,
        notes=[f"GetOrganelle retry profile: {json.dumps(profile, sort_keys=True)}"],
    )


def run_megahit(r1: Path, r2: Path, output_dir: Path, threads: int, reference: Path | None) -> Candidate | None:
    megahit_dir = output_dir / "megahit"
    if megahit_dir.exists():
        shutil.rmtree(megahit_dir)
    completed = run([
        "megahit", "-1", str(r1), "-2", str(r2), "-o", str(megahit_dir),
        "-t", str(threads), "--min-contig-len", "500",
    ])
    contigs = megahit_dir / "final.contigs.fa"
    if completed.returncode != 0 or not contigs.exists():
        return None
    records = load_records(contigs)
    if reference is not None:
        paf = megahit_dir / "reference.paf"
        rows = minimap_paf(reference, contigs, paf)
        supported = {row[0] for row in rows if int(row[9]) >= 500}
        records = [record for record in records if record.id in supported]
    if not records:
        return None
    records.sort(key=lambda record: len(record.seq), reverse=True)
    candidate_path = megahit_dir / "candidate.fasta"
    SeqIO.write(records, candidate_path, "fasta")
    length, count, n_fraction = fasta_metrics(candidate_path)
    return Candidate(
        name="megahit",
        method="independent_assembler",
        fasta=str(candidate_path),
        length=length,
        contig_count=count,
        n_fraction=n_fraction,
        notes=["Independent MEGAHIT assembly; reference-filtered when a reference was available."],
    )


def score_candidate(candidate: Candidate, minimum: int, maximum: int) -> float:
    midpoint = (minimum + maximum) / 2
    span = max(1.0, (maximum - minimum) / 2)
    length_score = max(0.0, 40.0 - 40.0 * abs(candidate.length - midpoint) / (midpoint + span))
    score = length_score
    if minimum <= candidate.length <= maximum:
        score += 20
    if candidate.circular:
        score += 25
    if candidate.graph_unique_path:
        score += 15
    score += 10 * (candidate.covered_fraction or 0.0)
    score += 10 * (candidate.reference_coverage or 0.0)
    score += 5 * (candidate.reference_identity or 0.0)
    score -= min(20.0, 3.0 * max(0, candidate.contig_count - 1))
    score -= 30.0 * candidate.n_fraction
    if candidate.method == "reference_guided_scaffolding":
        score -= 8.0
    candidate.score = round(score, 3)
    return candidate.score


def write_candidates_tsv(candidates: Iterable[Candidate], output: Path) -> None:
    fields = list(Candidate.__dataclass_fields__)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for candidate in candidates:
            row = candidate.to_dict()
            row["notes"] = " | ".join(candidate.notes)
            writer.writerow(row)


def write_report(sample_id: str, initial_status: str, selected: Candidate, candidates: list[Candidate], output: Path) -> None:
    lines = [
        "## Assembly rescue",
        "",
        f"- Initial status: **{initial_status}**",
        f"- Selected candidate: **{selected.name}**",
        f"- Method: `{selected.method}`",
        f"- Final score: **{selected.score:.3f}**",
        f"- Length: **{selected.length:,} bp**",
        f"- Contigs: **{selected.contig_count}**",
        f"- Circularity supported: **{'yes' if selected.circular else 'no'}**",
        "",
        "### Candidate comparison",
        "",
        "| Candidate | Method | Length | Contigs | Circular | Read coverage | Reference coverage | Score |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
        lines.append(
            f"| {candidate.name} | {candidate.method} | {candidate.length:,} | "
            f"{candidate.contig_count} | {'yes' if candidate.circular else 'no'} | "
            f"{candidate.covered_fraction if candidate.covered_fraction is not None else 'NA'} | "
            f"{candidate.reference_coverage if candidate.reference_coverage is not None else 'NA'} | "
            f"{candidate.score:.3f} |"
        )
    lines.extend([
        "",
        "### Interpretation",
        "",
        "A reference-guided draft is reported as a draft and is never treated as evidence of de novo circularization. "
        "Candidates that do not improve on the original remain available for review but are not promoted.",
        "",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
