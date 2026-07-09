"""run_markdown_report.py

Render run-level MitoPipeline reports.
"""

# Imports
import os
from pathlib import Path
from statistics import mean

from mitopipeline.models.report_data import SampleReportData
from mitopipeline.models.run_report_data import RunReportData
from mitopipeline.reporting.markdown_report import (
    escape_markdown_cell,
    format_integer,
    format_percent,
    markdown_table,
)


def relative_path(target_path: str | Path, report_path: str | Path) -> str:
    """Return a Markdown-safe report-relative path."""
    target_path = Path(target_path).resolve()
    report_path = Path(report_path).resolve()
    relative = os.path.relpath(target_path, start=report_path.parent)
    return Path(relative).as_posix()


def file_link(label: str, target_path: str | Path, report_path: str | Path) -> str | None:
    """Create a Markdown link when the target exists."""
    if target_path is None:
        return None

    target_path = Path(target_path)

    if not target_path.exists():
        return None

    return f"[{escape_markdown_cell(label)}]({relative_path(target_path, report_path)})"


def collect_numeric_values(sample_data: list[SampleReportData], stats_name: str, metric_name: str) -> list[float]:
    """Collect numeric values from sample report data."""
    values: list[float] = []

    for sample in sample_data:
        stats = getattr(sample, stats_name)

        if stats is None:
            continue

        value = stats.get(metric_name)

        if isinstance(value, (int, float)):
            values.append(float(value))

    return values


def render_run_overview_section(run_data: RunReportData) -> list[str]:
    """Render high-level run metadata."""
    successful_samples = sum(
        status.overall_status == "success"
        for status in run_data.sample_statuses
    )
    incomplete_samples = sum(
        status.overall_status != "success"
        for status in run_data.sample_statuses
    )

    rows = [
        ["Job ID", run_data.job_id],
        ["Generated", run_data.generated_at],
        ["Total samples", format_integer(run_data.total_samples)],
        ["Successful samples", format_integer(successful_samples)],
        ["Incomplete samples", format_integer(incomplete_samples)],
        ["Runtime manifest", str(run_data.runtime_manifest_path)],
    ]

    for key, value in run_data.run_metadata.items():
        rows.append([key, value])

    return [
        "## Run overview",
        "",
        markdown_table(headers=["Field", "Value"], rows=rows),
        "",
    ]


def render_stage_summary_section(run_data: RunReportData) -> list[str]:
    """Render per-stage success/missing counts."""
    if not run_data.stage_totals:
        return [
            "## Stage summary",
            "",
            "_No enabled stages were supplied to the run report._",
            "",
        ]

    rows = []

    for stage_name, totals in run_data.stage_totals.items():
        total = totals["total"]
        complete = totals["complete"]
        missing = totals["missing"]
        completion_rate = complete / total if total > 0 else 0.0
        rows.append([stage_name, complete, missing, format_percent(completion_rate, fraction=True)])

    return [
        "## Stage summary",
        "",
        markdown_table(
            headers=["Stage", "Complete", "Missing", "Completion rate"],
            rows=rows,
        ),
        "",
    ]


def render_sample_status_section(run_data: RunReportData, report_path: Path) -> list[str]:
    """Render status table for all samples."""
    rows = []

    for status in run_data.sample_statuses:
        missing_text = ", ".join(status.failed_stages) if status.failed_stages else "None"
        sample_report = (
            file_link("sample report", status.sample_report_path, report_path)
            if status.sample_report_path is not None
            else "Not available"
        )
        rows.append([
            status.sample_id,
            status.overall_status,
            f"{status.completed_stages}/{status.expected_stages}",
            missing_text,
            sample_report,
        ])

    return [
        "## Sample status",
        "",
        markdown_table(
            headers=["Sample", "Status", "Stages complete", "Missing stages", "Report"],
            rows=rows,
        ),
        "",
    ]


def render_failed_samples_section(run_data: RunReportData) -> list[str]:
    """Render a dedicated failed/incomplete sample section."""
    failed_statuses = [
        status
        for status in run_data.sample_statuses
        if status.overall_status != "success"
    ]

    lines = ["## Failed or incomplete samples", ""]

    if not failed_statuses:
        return [
            *lines,
            "No failed or incomplete samples were detected from available completion markers.",
            "",
        ]

    rows = [[status.sample_id, ", ".join(status.failed_stages)] for status in failed_statuses]

    return [
        *lines,
        markdown_table(headers=["Sample", "Missing stages"], rows=rows),
        "",
    ]


def render_read_summary_section(run_data: RunReportData) -> list[str]:
    """Render run-level trimming/read summary."""
    reads_in = collect_numeric_values(run_data.sample_data, "fastp_stats", "reads_in")
    reads_out = collect_numeric_values(run_data.sample_data, "fastp_stats", "reads_out")
    q30_out = collect_numeric_values(run_data.sample_data, "fastp_stats", "q30_rate_out")

    if not reads_in:
        return ["## Read trimming summary", "", "_fastp statistics were not available for this run._", ""]

    total_reads_in = sum(reads_in)
    total_reads_out = sum(reads_out)
    retention_rate = total_reads_out / total_reads_in if total_reads_in > 0 else 0.0
    rows = [
        ["Total reads before filtering", format_integer(total_reads_in)],
        ["Total reads after filtering", format_integer(total_reads_out)],
        ["Read retention rate", format_percent(retention_rate, fraction=True)],
    ]

    if q30_out:
        rows.append(["Mean post-filter Q30 rate", format_percent(mean(q30_out), fraction=True)])

    return ["## Read trimming summary", "", markdown_table(headers=["Metric", "Value"], rows=rows), ""]


def render_assembly_summary_section(run_data: RunReportData) -> list[str]:
    """Render run-level assembly summary."""
    total_lengths = collect_numeric_values(run_data.sample_data, "assembly_stats", "total_length_bp")
    contig_counts = collect_numeric_values(run_data.sample_data, "assembly_stats", "contig_count")
    gc_values = collect_numeric_values(run_data.sample_data, "assembly_stats", "gc_content_percent")

    if not total_lengths:
        return ["## Assembly summary", "", "_Assembly statistics were not available for this run._", ""]

    rows = [
        ["Samples with assemblies", format_integer(len(total_lengths))],
        ["Mean assembly length", f"{format_integer(mean(total_lengths))} bp"],
        ["Minimum assembly length", f"{format_integer(min(total_lengths))} bp"],
        ["Maximum assembly length", f"{format_integer(max(total_lengths))} bp"],
        ["Mean contig count", f"{mean(contig_counts):.2f}"],
        ["Mean GC content", format_percent(mean(gc_values))],
    ]

    per_sample_rows = []
    for sample in run_data.sample_data:
        stats = sample.assembly_stats
        if stats is None:
            per_sample_rows.append([sample.sample_id, "Not available", "Not available", "Not available", "Not available"])
            continue
        per_sample_rows.append([
            sample.sample_id,
            format_integer(stats["contig_count"]),
            f"{format_integer(stats['total_length_bp'])} bp",
            format_percent(stats["gc_content_percent"]),
            stats["circularization_status"] or "Unknown",
        ])

    return [
        "## Assembly summary",
        "",
        markdown_table(headers=["Metric", "Value"], rows=rows),
        "",
        "### Per-sample assembly statistics",
        "",
        markdown_table(headers=["Sample", "Contigs", "Length", "GC content", "Circularization"], rows=per_sample_rows),
        "",
    ]


def render_annotation_summary_section(run_data: RunReportData) -> list[str]:
    """Render run-level annotation summary."""
    annotation_samples = [sample for sample in run_data.sample_data if sample.annotation_stats is not None]

    if not annotation_samples:
        return ["## Annotation summary", "", "_Annotation statistics were not available for this run._", ""]

    feature_type_totals: dict[str, int] = {}
    per_sample_rows = []

    for sample in annotation_samples:
        stats = sample.annotation_stats
        for feature_type, count in stats["feature_counts"].items():
            feature_type_totals[feature_type] = feature_type_totals.get(feature_type, 0) + int(count)
        per_sample_rows.append([
            sample.sample_id,
            stats["total_features"],
            ", ".join(f"{feature_type}: {count}" for feature_type, count in stats["feature_counts"].items()),
        ])

    feature_rows = [[feature_type, count] for feature_type, count in sorted(feature_type_totals.items())]

    return [
        "## Annotation summary",
        "",
        markdown_table(headers=["Feature type", "Total count"], rows=feature_rows),
        "",
        "### Per-sample annotation statistics",
        "",
        markdown_table(headers=["Sample", "Total features", "Feature counts"], rows=per_sample_rows),
        "",
    ]


def render_phylogeny_summary_section(run_data: RunReportData) -> list[str]:
    """Render run-level phylogenetic summary."""
    phylogeny_samples = [
        sample
        for sample in run_data.sample_data
        if sample.phylogeny_tip_count is not None or sample.phylogeny_model is not None
    ]

    if not phylogeny_samples:
        return ["## Phylogenetic validation summary", "", "_Phylogenetic outputs were not available for this run._", ""]

    rows = [
        [
            sample.sample_id,
            sample.phylogeny_model or "Not available",
            sample.phylogeny_tip_count if sample.phylogeny_tip_count is not None else "Not available",
        ]
        for sample in run_data.sample_data
    ]

    return [
        "## Phylogenetic validation summary",
        "",
        markdown_table(headers=["Sample", "Selected model", "Tree tips"], rows=rows),
        "",
    ]


def render_manifest_metadata_summary_section(run_data: RunReportData) -> list[str]:
    """Render which metadata columns were included in the run."""
    rows = [[column] for column in run_data.metadata_columns]
    return [
        "## Runtime manifest metadata",
        "",
        "The run-level report was generated from the normalized runtime manifest.",
        "",
        markdown_table(headers=["Column"], rows=rows),
        "",
    ]


def render_output_links_section(run_data: RunReportData, report_path: Path) -> list[str]:
    """Render links to run-level artifacts."""
    rows = []
    for label, path_key in [
        ("Runtime manifest", "runtime_manifest"),
        ("Reporting directory", "reporting_directory"),
        ("Logs directory", "logs_directory"),
        ("Assembly directory", "assembly_directory"),
        ("Annotation directory", "annotation_directory"),
        ("Phylogeny directory", "phylogeny_directory"),
    ]:
        path = run_data.output_paths[path_key]
        link = file_link(label, path, report_path)
        if link is not None:
            rows.append([label, link])

    if not rows:
        return ["## Run output files", "", "_No run-level output links were available._", ""]

    return ["## Run output files", "", markdown_table(headers=["Output", "Path"], rows=rows), ""]


def render_run_report(run_data: RunReportData, report_path: str | Path) -> str:
    """Render a complete run-level Markdown report."""
    report_path = Path(report_path)
    lines = [
        f"# MitoPipeline Run Report: {run_data.job_id}",
        "",
        *render_run_overview_section(run_data),
        *render_stage_summary_section(run_data),
        *render_sample_status_section(run_data, report_path),
        *render_failed_samples_section(run_data),
        *render_read_summary_section(run_data),
        *render_assembly_summary_section(run_data),
        *render_annotation_summary_section(run_data),
        *render_phylogeny_summary_section(run_data),
        *render_manifest_metadata_summary_section(run_data),
        *render_output_links_section(run_data, report_path),
        "## Reproducibility",
        "",
        (
            "This run-level report was generated automatically from "
            "the normalized runtime manifest, per-sample reports, "
            "completion markers, and canonical MitoPipeline statistics parsers."
        ),
        "",
    ]
    return "\n".join(lines)


def write_run_report(run_data: RunReportData, output_path: str | Path) -> Path:
    """Write a run-level Markdown report atomically."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_run_report(run_data=run_data, report_path=output_path)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(report_text, encoding="utf-8")
    temporary_path.replace(output_path)
    return output_path
