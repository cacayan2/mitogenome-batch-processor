"""Render a circular map only for assemblies that pass completeness gating."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt

from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--assessment-json", required=True)
    parser.add_argument("--gff", required=True)
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--output-png", required=True)
    parser.add_argument("--output-svg", required=True)
    parser.add_argument("--output-pdf", required=True)
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def _write_incomplete_notice(args: argparse.Namespace, assessment: dict) -> None:
    status = assessment.get("status", "unknown")
    reason = assessment.get("reason", "No assessment reason was recorded.")
    primary_length = assessment.get("primary_contig_length", "unknown")
    fragment_count = assessment.get("mitochondrial_contig_count", "unknown")
    combined_length = assessment.get("mitochondrial_total_length", "unknown")

    text = (
        "Circular mitogenome map not generated\n\n"
        f"Sample: {args.sample_id}\n"
        f"Assembly status: {status}\n"
        f"Primary contig: {primary_length} bp\n"
        f"Mitochondrial fragments: {fragment_count}\n"
        f"Combined fragment length: {combined_length} bp\n\n"
        f"{reason}"
    )

    for output in (args.output_png, args.output_svg, args.output_pdf):
        Path(output).parent.mkdir(parents=True, exist_ok=True)

    figure = plt.figure(figsize=(11, 8.5))
    figure.text(
        0.5,
        0.5,
        text,
        ha="center",
        va="center",
        wrap=True,
        fontsize=14,
    )
    figure.savefig(args.output_png, dpi=args.dpi, bbox_inches="tight")
    figure.savefig(args.output_svg, bbox_inches="tight")
    figure.savefig(args.output_pdf, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    args = parse_args()
    logger = make_logger(
        f"assembly_visualization.{args.sample_id}",
        args.log_file,
    )

    try:
        assessment = json.loads(
            Path(args.assessment_json).read_text(encoding="utf-8")
        )

        if not assessment.get("circular_visualization_allowed", False):
            logger.warning(
                "Skipping circular genome map for %s because assembly "
                "status is %s.",
                args.sample_id,
                assessment.get("status", "unknown"),
            )
            _write_incomplete_notice(args, assessment)
            return 0

        command = [
            sys.executable,
            "-m",
            "mitopipeline.exec.generate_circular_genome_map",
            "--sample-id",
            args.sample_id,
            "--gff",
            args.gff,
            "--fasta",
            args.fasta,
            "--output-png",
            args.output_png,
            "--output-svg",
            args.output_svg,
            "--output-pdf",
            args.output_pdf,
            "--dpi",
            str(args.dpi),
            "--log-file",
            args.log_file,
        ]
        completed = subprocess.run(command, check=False)
        return completed.returncode

    except Exception as error:
        logger.exception("Assembly visualization failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
