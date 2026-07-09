"""Run local table2asn validation for mitogenome archival packages."""

from pathlib import Path


TABLE2ASN_CONFIG = config.get(
    "archival",
    {},
).get(
    "table2asn",
    {},
)


rule table2asn_validation:
    """Validate prepared mitogenome submission packages."""

    input:
        metadata=str(
            JOB_DIR
            / "submission"
            / "mitogenomes"
            / "mitogenome_metadata.tsv"
        ),
        template=lambda wildcards: TABLE2ASN_CONFIG[
            "submission_template"
        ]

    output:
        summary_tsv=str(
            JOB_DIR
            / "submission"
            / "table2asn"
            / "validation_summary.tsv"
        ),
        summary_md=str(
            JOB_DIR
            / "submission"
            / "table2asn"
            / "validation_summary.md"
        )

    params:
        output_directory=str(
            JOB_DIR
            / "submission"
            / "table2asn"
            / "samples"
        ),
        executable=TABLE2ASN_CONFIG.get(
            "executable",
            "table2asn",
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "archival"
                / "table2asn_validation.log"
            ).resolve()
        )

    conda:
        "../../envs/table2asn.yaml"

    shell:
        r"""

        python -m mitopipeline.exec.run_table2asn_validation \
            --mitogenome-metadata {input.metadata:q} \
            --submission-template {input.template:q} \
            --output-directory {params.output_directory:q} \
            --summary-tsv {output.summary_tsv:q} \
            --summary-markdown {output.summary_md:q} \
            --table2asn-bin {params.executable:q} \
            --log-file {params.log_file:q}
        """
