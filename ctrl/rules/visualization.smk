"""visualization.smk

Generate standardized circular mitochondrial genome maps from MITOS2 outputs.
"""

# Imports
from pathlib import Path


VISUALIZATION_CONFIG = config.get(
    "tools",
    {},
).get(
    "visualization",
    {},
)


rule circular_genome_map:
    """Generate circular mitochondrial genome map figures."""

    input:
        gff=str(
            JOB_DIR
            / "annotation"
            / "{sample}"
            / "result.gff"
        ),
        fasta=str(
            JOB_DIR
            / "assembly"
            / "{sample}"
            / "{sample}.fasta"
        ),
        annotation_done=str(
            JOB_DIR
            / "annotation"
            / "{sample}.annotation.done"
        )

    output:
        png=str(
            JOB_DIR
            / "visualization"
            / "{sample}.circular_mitogenome.png"
        ),
        svg=str(
            JOB_DIR
            / "visualization"
            / "{sample}.circular_mitogenome.svg"
        ),
        pdf=str(
            JOB_DIR
            / "visualization"
            / "{sample}.circular_mitogenome.pdf"
        ),
        done=str(
            JOB_DIR
            / "visualization"
            / "{sample}.visualization.done"
        )

    params:
        dpi=VISUALIZATION_CONFIG.get(
            "dpi",
            600,
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "visualization"
                / "{sample}.log"
            ).resolve()
        )

    conda:
        "../../envs/visualization.yaml"

    shell:
        """

        python -m mitopipeline.exec.generate_circular_genome_map \
            --sample-id {wildcards.sample} \
            --gff {input.gff} \
            --fasta {input.fasta} \
            --output-png {output.png} \
            --output-svg {output.svg} \
            --output-pdf {output.pdf} \
            --dpi {params.dpi} \
            --log-file {params.log_file}

        touch {output.done}
        """
