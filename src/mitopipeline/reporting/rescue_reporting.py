"""Markdown reporting helpers for automated assembly rescue."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json

def sample_rescue_section(job_directory: Path, sample_id: str) -> str:
    assembly_dir = job_directory / "assembly" / sample_id
    report = assembly_dir / "rescue_report.md"
    assessment = assembly_dir / "final_assembly_assessment.json"
    if report.exists():
        return report.read_text(encoding="utf-8").strip() + "\n"
    if not assessment.exists():
        return ""
    data = json.loads(assessment.read_text(encoding="utf-8"))
    selected = data.get("selected_candidate", {})
    return (
        "## Assembly rescue\n\n"
        f"- Initial status: **{data.get('initial_status', 'unknown')}**\n"
        f"- Final status: **{data.get('status', 'unknown')}**\n"
        f"- Rescue attempted: **{data.get('rescue_attempted', False)}**\n"
        f"- Rescue selected: **{data.get('rescue_selected', False)}**\n"
        f"- Selected method: `{selected.get('method', 'unknown')}`\n"
        f"- Selected length: **{selected.get('length', 'unknown')} bp**\n"
        f"- Circularity supported: **{data.get('circular_visualization_allowed', False)}**\n\n"
    )

def run_rescue_section(job_directory: Path) -> str:
    assembly_root = job_directory / "assembly"
    rows = []
    statuses: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    attempted = selected_count = 0
    for path in sorted(assembly_root.glob("*/final_assembly_assessment.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        sample_id = path.parent.name
        selected = data.get("selected_candidate", {})
        status = str(data.get("status", "unknown"))
        method = str(selected.get("method", "unknown"))
        statuses[status] += 1
        methods[method] += 1
        attempted += int(bool(data.get("rescue_attempted")))
        selected_count += int(bool(data.get("rescue_selected")))
        rows.append(
            f"| {sample_id} | {data.get('initial_status', 'unknown')} | {status} | "
            f"{method} | {selected.get('length', 'NA')} | "
            f"{'yes' if data.get('rescue_selected') else 'no'} | "
            f"{'yes' if data.get('circular_visualization_allowed') else 'no'} |"
        )
    if not rows:
        return ""
    lines = [
        "## Assembly rescue summary", "",
        f"- Samples assessed: **{len(rows)}**",
        f"- Rescue attempted: **{attempted}**",
        f"- Rescue candidate promoted: **{selected_count}**",
        f"- Final statuses: **{dict(statuses)}**",
        f"- Selected methods: **{dict(methods)}**", "",
        "| Sample | Initial status | Final status | Selected method | Length (bp) | Rescue promoted | Circular map allowed |",
        "| --- | --- | --- | --- | ---: | --- | --- |", *rows, "",
        "Reference-guided drafts are explicitly labeled and are not counted as de novo circular assemblies.", "",
    ]
    return "\n".join(lines)
