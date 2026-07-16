"""CLI for bounded, evidence-based mitochondrial assembly rescue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.rescue.assembly_rescue import (
    Candidate,
    circularize_terminal_overlap,
    fasta_metrics,
    fetch_reference,
    map_reads,
    reconstruct_gfa_path,
    reference_guided_draft,
    run_getorganelle_profile,
    run_megahit,
    score_candidate,
    write_candidates_tsv,
    write_report,
)


def boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean, received {value!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--r1", required=True)
    parser.add_argument("--r2", required=True)
    parser.add_argument("--initial-fasta", required=True)
    parser.add_argument("--fragments-fasta", required=True)
    parser.add_argument("--graph-gfa", required=True)
    parser.add_argument("--initial-assessment", required=True)
    parser.add_argument("--top-hits", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-fasta", required=True)
    parser.add_argument("--output-assessment", required=True)
    parser.add_argument("--output-metrics", required=True)
    parser.add_argument("--output-report", required=True)
    parser.add_argument("--reference-draft", required=True)
    parser.add_argument("--organelle-type", required=True)
    parser.add_argument("--entrez-email", default="")
    parser.add_argument("--entrez-api-key", default="")
    parser.add_argument("--enabled", type=boolean, default=True)
    parser.add_argument("--trigger-statuses", default="fragmented,partial")
    parser.add_argument("--profiles-json", default="[]")
    parser.add_argument("--complete-min-length", type=int, default=14000)
    parser.add_argument("--complete-max-length", type=int, default=22000)
    parser.add_argument("--minimum-score-improvement", type=float, default=5.0)
    parser.add_argument("--maximum-gap-size", type=int, default=5000)
    parser.add_argument("--reference-gap-n", type=int, default=100)
    parser.add_argument("--terminal-overlap-min", type=int, default=40)
    parser.add_argument("--terminal-overlap-max", type=int, default=1000)
    parser.add_argument("--terminal-overlap-identity", type=float, default=0.98)
    parser.add_argument("--run-read-mapping", type=boolean, default=True)
    parser.add_argument("--run-graph-resolution", type=boolean, default=True)
    parser.add_argument("--run-reference-scaffolding", type=boolean, default=True)
    parser.add_argument("--run-megahit", type=boolean, default=True)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = make_logger(f"assembly_rescue.{args.sample_id}", args.log_file)
    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        initial_assessment = json.loads(Path(args.initial_assessment).read_text(encoding="utf-8"))
        initial_status = str(initial_assessment.get("status", "unknown"))
        length, count, n_fraction = fasta_metrics(args.initial_fasta)
        original = Candidate(
            name="original",
            method="initial_getorganelle_selection",
            fasta=str(Path(args.initial_fasta)),
            length=length,
            contig_count=count,
            circular=bool(initial_assessment.get("circular_visualization_allowed", False)),
            n_fraction=n_fraction,
            notes=[str(initial_assessment.get("reason", ""))],
        )
        candidates = [original]
        triggers = {value.strip() for value in args.trigger_statuses.split(",") if value.strip()}
        should_rescue = args.enabled and initial_status in triggers

        reference = fetch_reference(
            Path(args.top_hits), args.entrez_email, args.entrez_api_key,
            output_dir / "reference.fasta",
        )

        overlap_candidate = circularize_terminal_overlap(
            Path(args.initial_fasta), output_dir / "terminal_overlap.fasta",
            args.terminal_overlap_min, args.terminal_overlap_max,
            args.terminal_overlap_identity,
        )
        if overlap_candidate:
            candidates.append(overlap_candidate)

        if should_rescue and args.run_graph_resolution:
            graph_candidate = reconstruct_gfa_path(
                Path(args.graph_gfa), Path(args.fragments_fasta),
                output_dir / "graph_resolved.fasta",
            )
            if graph_candidate:
                candidates.append(graph_candidate)

        if should_rescue and args.run_reference_scaffolding and reference:
            reference_candidate = reference_guided_draft(
                reference, Path(args.fragments_fasta), Path(args.reference_draft),
                output_dir / "fragments_to_reference.paf", args.reference_gap_n,
                args.maximum_gap_size,
            )
            if reference_candidate:
                candidates.append(reference_candidate)
        Path(args.reference_draft).touch(exist_ok=True)

        if should_rescue:
            for profile in json.loads(args.profiles_json):
                name = str(profile.get("name", f"profile_{len(candidates)}"))
                candidate = run_getorganelle_profile(
                    name, profile, Path(args.r1), Path(args.r2), output_dir,
                    args.organelle_type, args.threads,
                )
                if candidate:
                    candidates.append(candidate)

            if args.run_megahit:
                candidate = run_megahit(
                    Path(args.r1), Path(args.r2), output_dir, args.threads, reference,
                )
                if candidate:
                    candidates.append(candidate)

        if args.run_read_mapping:
            for candidate in candidates:
                evidence = map_reads(
                    Path(candidate.fasta), Path(args.r1), Path(args.r2),
                    output_dir / "mapping" / candidate.name, args.threads,
                )
                if evidence.get("available"):
                    candidate.mean_depth = evidence.get("mean_depth")
                    candidate.covered_fraction = evidence.get("covered_fraction")

        for candidate in candidates:
            score_candidate(candidate, args.complete_min_length, args.complete_max_length)

        original_score = original.score
        best = max(candidates, key=lambda candidate: candidate.score)
        if best is not original and best.score < original_score + args.minimum_score_improvement:
            best = original
            best.notes.append(
                "A rescue candidate scored higher, but not by the configured minimum improvement."
            )

        output_fasta = Path(args.output_fasta)
        output_fasta.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best.fasta, output_fasta)

        final_status = "complete_candidate" if (
            args.complete_min_length <= best.length <= args.complete_max_length
            and best.contig_count == 1
        ) else ("fragmented" if best.contig_count > 1 else "partial")
        circular_allowed = bool(best.circular and final_status == "complete_candidate")
        final = {
            **initial_assessment,
            "initial_status": initial_status,
            "status": final_status,
            "rescue_attempted": should_rescue,
            "rescue_selected": best.name != "original",
            "selected_candidate": best.to_dict(),
            "candidate_count": len(candidates),
            "circular_visualization_allowed": circular_allowed,
            "resolved_fasta": str(output_fasta),
            "reference_guided": best.method == "reference_guided_scaffolding",
            "warning": (
                "Reference-guided draft; circularity not confirmed."
                if best.method == "reference_guided_scaffolding"
                else None
            ),
        }
        Path(args.output_assessment).write_text(
            json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        write_candidates_tsv(candidates, Path(args.output_metrics))
        write_report(args.sample_id, initial_status, best, candidates, Path(args.output_report))
        logger.info(
            "[%s] Selected %s (%s; score %.3f) from %d candidates.",
            args.sample_id, best.name, best.method, best.score, len(candidates),
        )
        return 0
    except Exception as error:
        logger.exception("Automated assembly rescue failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
