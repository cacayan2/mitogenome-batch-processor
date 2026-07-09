"""Markdown-to-PDF reporting rules."""

from pathlib import Path


PDF_EXPORT_CONFIG = (
    config.get("tools", {}).get("pdf_export", {})
)


rule sample_report_pdf:
    input:
        markdown=str(
            JOB_DIR / "reporting" / "{sample}" / "report.md"
        )

    output:
        pdf=str(
            JOB_DIR / "reporting" / "{sample}" / "report.pdf"
        )

    params:
        job_directory=str(JOB_DIR),
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
                / "reporting"
                / "{sample}"
                / "pdf_export.log"
            ).resolve()
        )

    conda:
        "../../envs/pdf_export.yaml"

    shell:
        """
        python -m mitopipeline.exec.export_report_pdf \
            --markdown {input.markdown:q} \
            --pdf {output.pdf:q} \
            --job-directory {params.job_directory:q} \
            --pandoc-bin {params.pandoc_bin:q} \
            --pdf-engine {params.pdf_engine:q} \
            --log-file {params.log_file:q}

        test -s {output.pdf:q}
        """


rule run_report_pdf:
    input:
        markdown=str(
            JOB_DIR / "reporting" / "run" / "report.md"
        )

    output:
        pdf=str(
            JOB_DIR / "reporting" / "run" / "report.pdf"
        )

    params:
        job_directory=str(JOB_DIR),
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
                / "reporting"
                / "run"
                / "pdf_export.log"
            ).resolve()
        )

    conda:
        "../../envs/pdf_export.yaml"

    shell:
        """
        python -m mitopipeline.exec.export_report_pdf \
            --markdown {input.markdown:q} \
            --pdf {output.pdf:q} \
            --job-directory {params.job_directory:q} \
            --pandoc-bin {params.pandoc_bin:q} \
            --pdf-engine {params.pdf_engine:q} \
            --log-file {params.log_file:q}

        test -s {output.pdf:q}
        """
