"""Phylogeny dataset generation rule."""

from pathlib import Path


rule generate_alignment_dataset:
    input:
        assembly_fasta=str(
            JOB_DIR / "assembly" / "{sample}" / "selected.fasta"
        ),
        assembly_done=str(
            JOB_DIR / "assembly" / "{sample}" / "selection.done"
        ),
        top_hits=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.tsv"
        ),
        top_hits_done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.done"
        )

    output:
        dataset=str(
            JOB_DIR / "phylogeny" / "{sample}" / "dataset.fasta"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "dataset.done"
        )

    params:
        entrez_email=config["tools"]["blast"]["entrez_email"],
        entrez_api_key=(
            config["tools"]["blast"].get("entrez_api_key") or ""
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "dataset.log"
            ).resolve()
        )

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m mitopipeline.exec.generate_alignment_dataset \
            --sample-id {wildcards.sample} \
            --assembly-fasta {input.assembly_fasta:q} \
            --top-hits {input.top_hits:q} \
            --output-fasta {output.dataset:q} \
            --entrez-email "{params.entrez_email}" \
            --entrez-api-key "{params.entrez_api_key}" \
            --log-file {params.log_file:q}

        test -s {output.dataset:q}
        touch {output.done:q}
        """
