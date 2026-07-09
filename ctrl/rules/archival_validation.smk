"""Validate NCBI archival readiness."""

from pathlib import Path


rule archival_validation:
    """Write archival validation summary and Markdown report."""

    input:
        runtime_manifest=str(
            RUNTIME_MANIFEST_PATH
        )

    output:
        summary=str(
            JOB_DIR
            / "submission"
            / "validation_summary.tsv"
        ),
        report=str(
            JOB_DIR
            / "submission"
            / "validation_report.md"
        )

    params:
        job_directory=str(
            JOB_DIR
        ),
        submission_directory=str(
            JOB_DIR
            / "submission"
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "archival"
                / "validation.log"
            ).resolve()
        )

    shell:
        r"""

        python -m mitopipeline.exec.validate_archival_submission \
            --runtime-manifest {input.runtime_manifest:q} \
            --job-directory {params.job_directory:q} \
            --submission-directory {params.submission_directory:q} \
            --summary-output {output.summary:q} \
            --report-output {output.report:q} \
            --log-file {params.log_file:q}
        """
