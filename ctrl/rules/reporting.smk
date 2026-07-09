"""reporting.smk

Generate per-sample Markdown reports and one run-level Markdown report.
"""

# Imports
from pathlib import Path


def reporting_dependencies(wildcards) -> list[str]:
    """Return completion markers required by enabled stages."""
    dependencies = [str(RUNTIME_MANIFEST_PATH)]

    if stage_enabled("trimming"):
        dependencies.append(str(JOB_DIR / "trimming" / f"{wildcards.sample}.trimming.done"))

    if stage_enabled("assembly"):
        dependencies.append(str(JOB_DIR / "assembly" / f"{wildcards.sample}.assembly.done"))

    if stage_enabled("annotation"):
        dependencies.append(str(JOB_DIR / "annotation" / f"{wildcards.sample}.annotation.done"))

    if stage_enabled("phylogeny"):
        dependencies.append(str(JOB_DIR / "phylogeny" / "figures" / f"{wildcards.sample}.phylogeny.done"))

    return dependencies


def enabled_stage_names_for_run_report() -> list[str]:
    """Return stage names included in run-level status accounting."""
    stage_order = [
        "qc_raw",
        "trimming",
        "qc_trimmed",
        "assembly",
        "annotation",
        "phylogeny",
        "reporting",
    ]
    return [stage_name for stage_name in stage_order if stage_enabled(stage_name)]


rule reporting:
    """Generate one Markdown report for one sample."""
    input:
        reporting_dependencies
    output:
        report=str(JOB_DIR / "reporting" / "{sample}.report.md")
    params:
        job_directory=str(JOB_DIR),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "reporting" / "{sample}.log").resolve())
    conda:
        "../../envs/reporting.yaml"
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.generate_sample_report \
            --sample-id {wildcards.sample} \
            --job-directory {params.job_directory} \
            --output {output.report} \
            --log-file {params.log_file}
        """


rule run_report:
    """Generate one run-level Markdown report for the full job."""
    input:
        sample_reports=expand(str(JOB_DIR / "reporting" / "{sample}.report.md"), sample=SAMPLES),
        runtime_manifest=str(RUNTIME_MANIFEST_PATH)
    output:
        report=str(JOB_DIR / "reporting" / "run_report.md")
    params:
        job_id=JOB_ID,
        job_directory=str(JOB_DIR),
        enabled_stages=" ".join(enabled_stage_names_for_run_report()),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "reporting" / "run_report.log").resolve())
    conda:
        "../../envs/reporting.yaml"
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.generate_run_report \
            --job-id {params.job_id} \
            --job-directory {params.job_directory} \
            --enabled-stages {params.enabled_stages} \
            --output {output.report} \
            --log-file {params.log_file}
        """
