"""Circular mitogenome visualization rule."""

from pathlib import Path


VISUALIZATION_CONFIG = (
    config.get("tools", {}).get("visualization", {})
)


rule circular_genome_map:
    input:
        gff=str(JOB_DIR / "annotation" / "{sample}" / "result.gff"),
        fasta=str(JOB_DIR / "assembly" / "{sample}" / "data.fasta"),
        annotation_done=str(
            JOB_DIR / "annotation" / "{sample}" / "annotation.done"
        )

    output:
        png=str(
            JOB_DIR
            / "visualization"
            / "{sample}"
            / "circular_mitogenome.png"
        ),
        svg=str(
            JOB_DIR
            / "visualization"
            / "{sample}"
            / "circular_mitogenome.svg"
        ),
        pdf=str(
            JOB_DIR
            / "visualization"
            / "{sample}"
            / "circular_mitogenome.pdf"
        ),
        done=str(
            JOB_DIR
            / "visualization"
            / "{sample}"
            / "visualization.done"
        )

    params:
        dpi=VISUALIZATION_CONFIG.get("dpi", 600),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "visualization"
                / "{sample}"
                / "visualization.log"
            ).resolve()
        )

    conda:
        "../../envs/visualization.yaml"

    shell:
        """
        python -m mitopipeline.exec.generate_circular_genome_map \
            --sample-id {wildcards.sample} \
            --gff {input.gff:q} \
            --fasta {input.fasta:q} \
            --output-png {output.png:q} \
            --output-svg {output.svg:q} \
            --output-pdf {output.pdf:q} \
            --dpi {params.dpi} \
            --log-file {params.log_file:q}

        test -s {output.png:q}
        test -s {output.svg:q}
        test -s {output.pdf:q}
        touch {output.done:q}
        """
