"""reporting.smk

Generate one Markdown report per sample from available pipeline outputs.
"""

# Imports
from pathlib import Path


def reporting_dependencies(
        wildcards,
) -> list[str]:
    """Return completion markers required by enabled stages."""
    dependencies = [
        str(
            RUNTIME_MANIFEST_PATH
        ),
    ]

    if stage_enabled(
        "trimming"
    ):
        dependencies.append(
            str(
                JOB_DIR
                / "trimming"
                / f"{wildcards.sample}.trimming.done"
            )
        )

    if stage_enabled(
        "assembly"
    ):
        dependencies.append(
            str(
                JOB_DIR
                / "assembly"
                / f"{wildcards.sample}.assembly.done"
            )
        )

    if stage_enabled(
        "annotation"
    ):
        dependencies.append(
            str(
                JOB_DIR
                / "annotation"
                / f"{wildcards.sample}.annotation.done"
            )
        )

    if stage_enabled(
        "phylogeny"
    ):
        dependencies.append(
            str(
                JOB_DIR
                / "phylogeny"
                / "figures"
                / f"{wildcards.sample}.phylogeny.done"
            )
        )

    return dependencies


rule reporting:
    """Generate one Markdown report for one sample."""

    input:
        reporting_dependencies

    output:
        report=str(
            JOB_DIR
            / "reporting"
            / "{sample}.report.md"
        )

    params:
        job_directory=str(
            JOB_DIR
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "reporting"
                / "{sample}.log"
            ).resolve()
        )

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