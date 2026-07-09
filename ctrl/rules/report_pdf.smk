"""report_pdf.smk

Convert Markdown reports to PDF using Pandoc with Typst.
"""

# Imports
from pathlib import Path


PDF_EXPORT_CONFIG = config.get(
    "tools",
    {},
).get(
    "pdf_export",
    {},
)


rule sample_report_pdf:
    """Convert one per-sample Markdown report to PDF."""

    input:
        markdown=str(
            JOB_DIR
            / "reporting"
            / "{sample}.report.md"
        )

    output:
        pdf=str(
            JOB_DIR
            / "reporting"
            / "{sample}.report.pdf"
        )

    params:
        job_directory=str(
            JOB_DIR
        ),
        pandoc_bin=PDF_EXPORT_CONFIG.get(
            "pandoc_bin",
            "pandoc",
        ),
        pdf_engine=PDF_EXPORT_CONFIG.get(
            "pdf_engine",
            "typst",
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "pdf_export"
                / "{sample}.log"
            ).resolve()
        )

    conda:
        "../../envs/pdf_export.yaml"

    shell:
        """

        python -m mitopipeline.exec.export_report_pdf \
            --markdown {input.markdown} \
            --pdf {output.pdf} \
            --job-directory {params.job_directory} \
            --pandoc-bin {params.pandoc_bin} \
            --pdf-engine {params.pdf_engine} \
            --log-file {params.log_file}
        """


rule run_report_pdf:
    """Convert the run-level Markdown report to PDF."""

    input:
        markdown=str(
            JOB_DIR
            / "reporting"
            / "run_report.md"
        )

    output:
        pdf=str(
            JOB_DIR
            / "reporting"
            / "run_report.pdf"
        )

    params:
        job_directory=str(
            JOB_DIR
        ),
        pandoc_bin=PDF_EXPORT_CONFIG.get(
            "pandoc_bin",
            "pandoc",
        ),
        pdf_engine=PDF_EXPORT_CONFIG.get(
            "pdf_engine",
            "typst",
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "pdf_export"
                / "run_report.log"
            ).resolve()
        )

    conda:
        "../../envs/pdf_export.yaml"

    shell:
        """

        python -m mitopipeline.exec.export_report_pdf \
            --markdown {input.markdown} \
            --pdf {output.pdf} \
            --job-directory {params.job_directory} \
            --pandoc-bin {params.pandoc_bin} \
            --pdf-engine {params.pdf_engine} \
            --log-file {params.log_file}
        """
