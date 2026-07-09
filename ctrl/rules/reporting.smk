"""Per-sample and run-level Markdown reporting rules."""

from pathlib import Path


def reporting_dependencies(wildcards) -> list[str]:
    dependencies = [str(RUNTIME_MANIFEST_PATH)]

    if stage_enabled("trimming"):
        dependencies.append(
            str(
                JOB_DIR
                / "trimming"
                / wildcards.sample
                / "trimming.done"
            )
        )

    if stage_enabled("assembly"):
        dependencies.append(
            str(
                JOB_DIR
                / "assembly"
                / wildcards.sample
                / "assembly.done"
            )
        )

    if stage_enabled("annotation"):
        dependencies.append(
            str(
                JOB_DIR
                / "annotation"
                / wildcards.sample
                / "annotation.done"
            )
        )

    if stage_enabled("phylogeny"):
        dependencies.append(
            str(
                JOB_DIR
                / "phylogeny"
                / wildcards.sample
                / "phylogeny.done"
            )
        )

    return dependencies


def enabled_stage_names_for_run_report() -> list[str]:
    stage_order = [
        "qc_raw",
        "trimming",
        "qc_trimmed",
        "assembly",
        "annotation",
        "visualization",
        "phylogeny",
        "reporting",
    ]
    return [
        stage
        for stage in stage_order
        if stage_enabled(stage)
    ]


rule reporting:
    input:
        reporting_dependencies

    output:
        report=str(
            JOB_DIR / "reporting" / "{sample}" / "report.md"
        )

    params:
        job_directory=str(JOB_DIR),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "reporting"
                / "{sample}"
                / "reporting.log"
            ).resolve()
        )

    conda:
        "../../envs/reporting.yaml"

    shell:
        """
        python -m mitopipeline.exec.generate_sample_report \
            --sample-id {wildcards.sample} \
            --job-directory {params.job_directory:q} \
            --output {output.report:q} \
            --log-file {params.log_file:q}

        test -s {output.report:q}
        """


rule run_report:
    input:
        sample_reports=expand(
            str(
                JOB_DIR
                / "reporting"
                / "{sample}"
                / "report.md"
            ),
            sample=SAMPLES,
        ),
        runtime_manifest=str(RUNTIME_MANIFEST_PATH)

    output:
        report=str(
            JOB_DIR / "reporting" / "run" / "report.md"
        )

    params:
        job_id=JOB_ID,
        job_directory=str(JOB_DIR),
        enabled_stages=" ".join(
            enabled_stage_names_for_run_report()
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "reporting"
                / "run"
                / "reporting.log"
            ).resolve()
        )

    conda:
        "../../envs/reporting.yaml"

    shell:
        """
        python -m mitopipeline.exec.generate_run_report \
            --job-id {params.job_id} \
            --job-directory {params.job_directory:q} \
            --enabled-stages {params.enabled_stages} \
            --output {output.report:q} \
            --log-file {params.log_file:q}

        test -s {output.report:q}
        """
