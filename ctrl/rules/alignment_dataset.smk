"""alignment_dataset.smk

Contains the rule for generating combined phylogenetic FASTA datasets.
"""

# Imports
from pathlib import Path


rule generate_alignment_dataset:
    """Combine an assembled genome with selected BLAST references.

    Inputs:
        assembly_fasta: Assembled mitochondrial-genome FASTA.
        assembly_done: Assembly-stage completion marker.
        top_hits: Selected BLAST-hit TSV.
        top_hits_done: BLAST-hit-selection completion marker.

    Outputs:
        dataset: Combined unaligned phylogenetic FASTA.
        done: Alignment-dataset completion marker.
    """
    # Inputs
    input:
        assembly_fasta=str(
            JOB_DIR
            / "assembly"
            / "{sample}"
            / "{sample}.fasta"
        ),
        assembly_done=str(
            JOB_DIR
            / "assembly"
            / "{sample}.assembly.done"
        ),
        top_hits=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.top_hits.tsv"
        ),
        top_hits_done=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.top_hits.done"
        )

    # Outputs
    output:
        dataset=str(
            JOB_DIR
            / "phylogeny"
            / "datasets"
            / "{sample}.phylogeny.fasta"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "datasets"
            / "{sample}.phylogeny.done"
        )

    # Parameters
    params:
        entrez_email=config["tools"]["blast"][
            "entrez_email"
        ],
        entrez_api_key=(
            config["tools"]["blast"].get(
                "entrez_api_key"
            )
            or ""
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "alignment_dataset"
                / "{sample}.log"
            ).resolve()
        )

    # Conda environment
    conda:
        "../../envs/mitopipeline.yaml"

    # Execution
    shell:
        """

        python -m mitopipeline.exec.generate_alignment_dataset \
            --sample-id {wildcards.sample} \
            --assembly-fasta {input.assembly_fasta} \
            --top-hits {input.top_hits} \
            --output-fasta {output.dataset} \
            --entrez-email "{params.entrez_email}" \
            --entrez-api-key "{params.entrez_api_key}" \
            --log-file {params.log_file}

        touch {output.done}
        """