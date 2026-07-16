"""Automated rescue and evidence-based selection of mitochondrial assemblies."""

from pathlib import Path
import json
import shlex


RESCUE_CONFIG = config.get("assembly_rescue", {})


def rescue_profiles_json() -> str:
    return shlex.quote(json.dumps(RESCUE_CONFIG.get("getorganelle_profiles", [])))


def rescue_bool(name: str, default: bool = True) -> str:
    return "true" if RESCUE_CONFIG.get(name, default) else "false"


rule rescue_mitochondrial_assembly:
    input:
        r1=str(JOB_DIR / "trimming" / "{sample}" / "R1.trimmed.fastq.gz"),
        r2=str(JOB_DIR / "trimming" / "{sample}" / "R2.trimmed.fastq.gz"),
        initial_fasta=str(JOB_DIR / "assembly" / "{sample}" / "selected.fasta"),
        fragments_fasta=str(JOB_DIR / "assembly" / "{sample}" / "mitochondrial_fragments.fasta"),
        graph=str(JOB_DIR / "assembly" / "{sample}" / "graph.gfa"),
        assessment=str(JOB_DIR / "assembly" / "{sample}" / "assembly_assessment.json"),
        selection_done=str(JOB_DIR / "assembly" / "{sample}" / "selection.done"),
        top_hits=str(JOB_DIR / "phylogeny" / "{sample}" / "top_hits.tsv"),
        top_hits_done=str(JOB_DIR / "phylogeny" / "{sample}" / "top_hits.done")

    output:
        fasta=str(JOB_DIR / "assembly" / "{sample}" / "resolved.fasta"),
        assessment=str(JOB_DIR / "assembly" / "{sample}" / "final_assembly_assessment.json"),
        metrics=str(JOB_DIR / "assembly" / "{sample}" / "rescue_candidates.tsv"),
        report=str(JOB_DIR / "assembly" / "{sample}" / "rescue_report.md"),
        reference_draft=str(JOB_DIR / "assembly" / "{sample}" / "reference_guided_draft.fasta"),
        done=str(JOB_DIR / "assembly" / "{sample}" / "rescue.done")

    params:
        output_dir=str(JOB_DIR / "assembly" / "{sample}" / "rescue"),
        organelle_type=config["tools"]["getorganelle"]["database_type"],
        entrez_email=config["tools"]["blast"]["entrez_email"],
        entrez_api_key=config["tools"]["blast"].get("entrez_api_key") or "",
        enabled=rescue_bool("enabled", True),
        trigger_statuses=",".join(RESCUE_CONFIG.get("trigger_statuses", ["fragmented", "partial"])),
        profiles=rescue_profiles_json(),
        complete_min_length=RESCUE_CONFIG.get("complete_min_length", 14000),
        complete_max_length=RESCUE_CONFIG.get("complete_max_length", 22000),
        minimum_score_improvement=RESCUE_CONFIG.get("minimum_score_improvement", 5.0),
        maximum_gap_size=RESCUE_CONFIG.get("maximum_gap_size", 5000),
        reference_gap_n=RESCUE_CONFIG.get("reference_gap_n", 100),
        terminal_overlap_min=RESCUE_CONFIG.get("terminal_overlap_min", 40),
        terminal_overlap_max=RESCUE_CONFIG.get("terminal_overlap_max", 1000),
        terminal_overlap_identity=RESCUE_CONFIG.get("terminal_overlap_identity", 0.98),
        run_read_mapping=rescue_bool("run_read_mapping", True),
        run_graph_resolution=rescue_bool("run_graph_resolution", True),
        run_reference_scaffolding=rescue_bool("run_reference_scaffolding", True),
        run_megahit=rescue_bool("run_megahit", True),
        log_file=str(JOB_DIR / "assembly" / "{sample}" / "rescue.log")

    threads:
        config["tools"]["getorganelle"]["threads"]

    conda:
        "../../envs/rescue.yaml"

    shell:
        r"""
        set -euo pipefail

        python -m mitopipeline.exec.rescue_mitochondrial_assembly \
            --sample-id {wildcards.sample:q} \
            --r1 {input.r1:q} \
            --r2 {input.r2:q} \
            --initial-fasta {input.initial_fasta:q} \
            --fragments-fasta {input.fragments_fasta:q} \
            --graph-gfa {input.graph:q} \
            --initial-assessment {input.assessment:q} \
            --top-hits {input.top_hits:q} \
            --output-dir {params.output_dir:q} \
            --output-fasta {output.fasta:q} \
            --output-assessment {output.assessment:q} \
            --output-metrics {output.metrics:q} \
            --output-report {output.report:q} \
            --reference-draft {output.reference_draft:q} \
            --organelle-type {params.organelle_type:q} \
            --entrez-email {params.entrez_email:q} \
            --entrez-api-key {params.entrez_api_key:q} \
            --enabled {params.enabled} \
            --trigger-statuses {params.trigger_statuses:q} \
            --profiles-json {params.profiles} \
            --complete-min-length {params.complete_min_length} \
            --complete-max-length {params.complete_max_length} \
            --minimum-score-improvement {params.minimum_score_improvement} \
            --maximum-gap-size {params.maximum_gap_size} \
            --reference-gap-n {params.reference_gap_n} \
            --terminal-overlap-min {params.terminal_overlap_min} \
            --terminal-overlap-max {params.terminal_overlap_max} \
            --terminal-overlap-identity {params.terminal_overlap_identity} \
            --run-read-mapping {params.run_read_mapping} \
            --run-graph-resolution {params.run_graph_resolution} \
            --run-reference-scaffolding {params.run_reference_scaffolding} \
            --run-megahit {params.run_megahit} \
            --threads {threads} \
            --log-file {params.log_file:q}

        test -s {output.fasta:q}
        test -s {output.assessment:q}
        test -s {output.metrics:q}
        test -s {output.report:q}
        test -e {output.reference_draft:q}
        touch {output.done:q}
        """
