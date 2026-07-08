"""markdown_report.py

Render aggregated pipeline results as per-sample Markdown reports.
"""

# Imports
import os
from datetime import datetime, timezone
from pathlib import Path

from mitopipeline.models.report_data import (
    SampleReportData,
)


def escape_markdown_cell(
        value: object,
) -> str:
    """Escape a value for use in a Markdown table."""
    return (
        str(value)
        .replace(
            "|",
            "\\|",
        )
        .replace(
            "\n",
            " ",
        )
        .strip()
    )


def markdown_table(
        headers: list[str],
        rows: list[list[object]],
) -> str:
    """Render a GitHub-compatible Markdown table."""
    header = (
        "| "
        + " | ".join(
            escape_markdown_cell(
                value
            )
            for value in headers
        )
        + " |"
    )

    separator = (
        "| "
        + " | ".join(
            "---"
            for _ in headers
        )
        + " |"
    )

    body = [
        (
            "| "
            + " | ".join(
                escape_markdown_cell(
                    value
                )
                for value in row
            )
            + " |"
        )
        for row in rows
    ]

    return "\n".join(
        [
            header,
            separator,
            *body,
        ]
    )


def format_integer(
        value: int | float,
) -> str:
    """Format an integer-like value."""
    return f"{value:,.0f}"


def format_percent(
        value: float,
        fraction: bool = False,
) -> str:
    """Format a percentage value."""
    if fraction:
        value *= 100.0

    return f"{value:.2f}%"


def relative_path(
        target_path: str | Path,
        report_path: str | Path,
) -> str:
    """Return a Markdown-safe report-relative path."""
    target_path = Path(
        target_path
    ).resolve()

    report_path = Path(
        report_path
    ).resolve()

    relative = os.path.relpath(
        target_path,
        start=report_path.parent,
    )

    return Path(
        relative
    ).as_posix()


def file_link(
        label: str,
        target_path: str | Path,
        report_path: str | Path,
) -> str | None:
    """Create a Markdown file link when the target exists."""
    target_path = Path(
        target_path
    )

    if not target_path.exists():
        return None

    return (
        f"[{label}]"
        f"({relative_path(target_path, report_path)})"
    )


def render_metadata_section(
        report_data: SampleReportData,
) -> list[str]:
    """Render runtime-manifest metadata."""
    rows = [
        [
            key,
            value,
        ]
        for key, value in report_data.metadata.items()
    ]

    return [
        "## Sample metadata",
        "",
        markdown_table(
            headers=[
                "Field",
                "Value",
            ],
            rows=rows,
        ),
        "",
    ]

def format_scientific_name(metadata: dict[str, str]) -> str:
    """Format genus, species, and subspecies from manifest metadata."""
    genus = metadata.get("genus", "").strip()
    species = metadata.get("species", "").strip()
    subspecies = metadata.get("subspecies", "").strip()

    parts = [genus, species]

    if subspecies.lower() not in {"", "na", "n/a", "none", "null"}:
        parts.append(subspecies)

    scientific_name = " ".join(part for part in parts if part)

    return scientific_name or metadata.get("scientific_name", "Not provided")

def render_fastp_section(
        report_data: SampleReportData,
) -> list[str]:
    """Render canonical fastp statistics."""
    stats = report_data.fastp_stats

    lines = [
        "## Read trimming and filtering",
        "",
    ]

    if stats is None:
        return [
            *lines,
            "_fastp statistics were not available._",
            "",
        ]

    lines.extend(
        [
            markdown_table(
                headers=[
                    "Metric",
                    "Before filtering",
                    "After filtering",
                ],
                rows=[
                    [
                        "Reads",
                        format_integer(
                            stats["reads_in"]
                        ),
                        format_integer(
                            stats["reads_out"]
                        ),
                    ],
                    [
                        "Bases",
                        format_integer(
                            stats["bases_in"]
                        ),
                        format_integer(
                            stats["bases_out"]
                        ),
                    ],
                    [
                        "Q20 rate",
                        format_percent(
                            stats[
                                "q20_rate_in"
                            ],
                            fraction=True,
                        ),
                        format_percent(
                            stats[
                                "q20_rate_out"
                            ],
                            fraction=True,
                        ),
                    ],
                    [
                        "Q30 rate",
                        format_percent(
                            stats[
                                "q30_rate_in"
                            ],
                            fraction=True,
                        ),
                        format_percent(
                            stats[
                                "q30_rate_out"
                            ],
                            fraction=True,
                        ),
                    ],
                    [
                        "GC content",
                        format_percent(
                            stats[
                                "gc_content_in"
                            ],
                            fraction=True,
                        ),
                        format_percent(
                            stats[
                                "gc_content_out"
                            ],
                            fraction=True,
                        ),
                    ],
                ],
            ),
            "",
            (
                f"- Read retention: "
                f"{format_percent(stats['read_retention_rate'], fraction=True)}"
            ),
            (
                f"- Base retention: "
                f"{format_percent(stats['base_retention_rate'], fraction=True)}"
            ),
            (
                f"- Reads removed: "
                f"{format_integer(stats['reads_removed'])}"
            ),
            (
                f"- Bases removed: "
                f"{format_integer(stats['bases_removed'])}"
            ),
            (
                f"- Low-quality reads removed: "
                f"{format_integer(stats['low_qual_removed'])}"
            ),
            (
                f"- Reads with too many N bases removed: "
                f"{format_integer(stats['too_many_n_removed'])}"
            ),
            (
                f"- Reads that were too short: "
                f"{format_integer(stats['too_short_removed'])}"
            ),
            (
                f"- Adapter-trimmed reads: "
                f"{format_integer(stats['adapter_removed_reads'])}"
            ),
            "",
        ]
    )

    return lines


def render_assembly_section(
        report_data: SampleReportData,
) -> list[str]:
    """Render canonical assembly statistics."""
    stats = report_data.assembly_stats

    lines = [
        "## Assembly",
        "",
    ]

    if stats is None:
        return [
            *lines,
            "_Assembly statistics were not available._",
            "",
        ]

    circularization = (
        stats["circularization_status"]
        if stats["circularization_status"]
        is not None
        else "Unknown"
    )

    rows = [
        [
            "Contig count",
            format_integer(
                stats["contig_count"]
            ),
        ],
        [
            "Total length",
            (
                f"{format_integer(stats['total_length_bp'])} bp"
            ),
        ],
        [
            "GC content",
            format_percent(
                stats[
                    "gc_content_percent"
                ]
            ),
        ],
        [
            "Circularization status",
            circularization,
        ],
    ]

    if stats.get(
        "runtime_seconds"
    ) is not None:
        rows.append(
            [
                "Assembly runtime",
                (
                    f"{stats['runtime_seconds']:.2f} seconds"
                ),
            ]
        )

    return [
        *lines,
        markdown_table(
            headers=[
                "Metric",
                "Value",
            ],
            rows=rows,
        ),
        "",
    ]


def render_annotation_section(
        report_data: SampleReportData,
) -> list[str]:
    """Render annotation statistics."""
    stats = report_data.annotation_stats

    lines = [
        "## Annotation",
        "",
    ]

    if stats is None:
        return [
            *lines,
            "_Annotation statistics were not available._",
            "",
        ]

    feature_rows = [
        [
            feature_type,
            count,
        ]
        for feature_type, count in stats[
            "feature_counts"
        ].items()
    ]

    lines.extend(
        [
            (
                f"Total annotated features: "
                f"**{stats['total_features']}**"
            ),
            "",
            markdown_table(
                headers=[
                    "Feature type",
                    "Count",
                ],
                rows=feature_rows,
            ),
            "",
        ]
    )

    if stats[
        "feature_names"
    ]:
        lines.extend(
            [
                "### Annotated features",
                "",
                ", ".join(
                    f"`{name}`"
                    for name in stats[
                        "feature_names"
                    ]
                ),
                "",
            ]
        )

    return lines


def render_blast_section(
        report_data: SampleReportData,
) -> list[str]:
    """Render ranked BLAST results."""
    matches = report_data.blast_matches

    lines = [
        "## Closest BLAST matches",
        "",
    ]

    if not matches:
        return [
            *lines,
            "_Ranked BLAST results were not available._",
            "",
        ]

    rows = [
        [
            match["rank"],
            match["sscinames"]
            or "Not reported",
            match["sseqid"],
            f"{match['pident']:.2f}%",
            f"{match['qcovs']:.2f}%",
            match["length"],
            f"{match['evalue']:.3g}",
            f"{match['bitscore']:.1f}",
        ]
        for match in matches
    ]

    return [
        *lines,
        markdown_table(
            headers=[
                "Rank",
                "Scientific name",
                "Accession",
                "Identity",
                "Query coverage",
                "Alignment length",
                "E-value",
                "Bit score",
            ],
            rows=rows,
        ),
        "",
    ]


def render_phylogeny_section(
        report_data: SampleReportData,
        report_path: Path,
) -> list[str]:
    """Render phylogenetic summary and existing figures."""
    paths = report_data.output_paths

    lines = [
        "## Phylogenetic validation",
        "",
    ]

    links = [
        link
        for link in [
            file_link(
                "Unaligned phylogeny dataset",
                paths["phylogeny_dataset"],
                report_path,
            ),
            file_link(
                "MAFFT alignment",
                paths["alignment_fasta"],
                report_path,
            ),
            file_link(
                "IQ-TREE report",
                paths["iqtree_report"],
                report_path,
            ),
            file_link(
                "Newick tree",
                paths["newick_tree"],
                report_path,
            ),
            file_link(
                "SVG tree figure",
                paths["tree_svg"],
                report_path,
            ),
            file_link(
                "PDF tree figure",
                paths["tree_pdf"],
                report_path,
            ),
            file_link(
                "PNG tree figure",
                paths["tree_png"],
                report_path,
            ),
            file_link(
                "Phylogeny methods summary",
                paths["phylogeny_summary"],
                report_path,
            ),
        ]
        if link is not None
    ]

    if not links:
        return [
            *lines,
            "_Phylogenetic outputs were not available._",
            "",
        ]

    if report_data.phylogeny_model is not None:
        lines.append(
            f"- Selected model: "
            f"`{report_data.phylogeny_model}`"
        )

    if report_data.phylogeny_tip_count is not None:
        lines.append(
            f"- Tree tips: "
            f"{report_data.phylogeny_tip_count}"
        )

    lines.extend(
        [
            "- " + "\n- ".join(
                links
            ),
            "",
        ]
    )

    if paths[
        "tree_png"
    ].exists():
        image_path = relative_path(
            paths["tree_png"],
            report_path,
        )

        lines.extend(
            [
                "### Maximum-likelihood tree",
                "",
                (
                    "![Maximum-likelihood mitochondrial "
                    f"phylogeny]({image_path})"
                ),
                "",
            ]
        )

    return lines


def render_output_section(
        report_data: SampleReportData,
        report_path: Path,
) -> list[str]:
    """Render links to major output artifacts."""
    output_labels = {
        "fastp_html": "fastp HTML report",
        "fastp_json": "fastp JSON output",
        "assembly_fasta": "Assembly FASTA",
        "blast_top_hits": "Ranked BLAST matches",
        "alignment_fasta": "Aligned FASTA",
        "iqtree_report": "IQ-TREE report",
        "newick_tree": "Newick tree",
        "tree_svg": "SVG tree figure",
        "tree_pdf": "PDF tree figure",
        "tree_png": "PNG tree figure",
    }

    rows: list[list[str]] = []

    for path_name, label in output_labels.items():
        link = file_link(
            label=label,
            target_path=report_data.output_paths[
                path_name
            ],
            report_path=report_path,
        )

        if link is not None:
            rows.append(
                [
                    label,
                    link,
                ]
            )

    if report_data.annotation_stats is not None:
        annotation_path = Path(
            report_data.annotation_stats[
                "gff_path"
            ]
        )

        link = file_link(
            label="Annotation GFF",
            target_path=annotation_path,
            report_path=report_path,
        )

        if link is not None:
            rows.append(
                [
                    "Annotation GFF",
                    link,
                ]
            )

    lines = [
        "## Output files",
        "",
    ]

    if not rows:
        return [
            *lines,
            "_No output artifacts were available._",
            "",
        ]

    return [
        *lines,
        markdown_table(
            headers=[
                "Output",
                "File",
            ],
            rows=rows,
        ),
        "",
    ]


def render_sample_report(
        report_data: SampleReportData,
        report_path: str | Path,
) -> str:
    """Render a complete sample Markdown report.

    Args:
        report_data (SampleReportData): Aggregated sample data.
        report_path (str | Path): Final report location.

    Returns:
        str: Complete Markdown report.
    """
    report_path = Path(
        report_path
    )

    species = format_scientific_name(
    report_data.metadata
    )
    
    generated_at = datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )

    lines = [
        (
            "# Mitochondrial Genome Report: "
            f"{report_data.sample_id}"
        ),
        "",
        f"**Sample ID:** `{report_data.sample_id}`  ",
        f"**Species:** {species}  ",
        f"**Generated:** {generated_at}  ",
        "",
        *render_metadata_section(
            report_data
        ),
        *render_fastp_section(
            report_data
        ),
        *render_assembly_section(
            report_data
        ),
        *render_annotation_section(
            report_data
        ),
        *render_blast_section(
            report_data
        ),
        *render_phylogeny_section(
            report_data,
            report_path,
        ),
        *render_output_section(
            report_data,
            report_path,
        ),
        "## Reproducibility",
        "",
        (
            "This report was generated automatically from the "
            "normalized runtime manifest and the canonical statistics "
            "parsers used by MitoPipeline."
        ),
        "",
    ]

    return "\n".join(
        lines
    )


def write_sample_report(
        report_data: SampleReportData,
        output_path: str | Path,
) -> Path:
    """Write a sample report atomically.

    Args:
        report_data (SampleReportData): Aggregated sample data.
        output_path (str | Path): Markdown output path.

    Returns:
        Path: Written report path.
    """
    output_path = Path(
        output_path
    ).resolve()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_text = render_sample_report(
        report_data=report_data,
        report_path=output_path,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    temporary_path.write_text(
        report_text,
        encoding="utf-8",
    )

    temporary_path.replace(
        output_path
    )

    return output_path