"""Mitochondrial-contig selection rule."""

from pathlib import Path


rule select_mitochondrial_contig:
    input:
        assembly_fasta=str(
            JOB_DIR / "assembly" / "{sample}" / "data.fasta"
        ),
        assembly_done=str(
            JOB_DIR / "assembly" / "{sample}" / "assembly.done"
        ),
        top_hits=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.tsv"
        ),
        top_hits_done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.done"
        )

    output:
        fasta=str(
            JOB_DIR / "assembly" / "{sample}" / "selected.fasta"
        ),
        done=str(
            JOB_DIR / "assembly" / "{sample}" / "selection.done"
        )

    params:
        log_file=str(
            JOB_DIR
            / "assembly"
            / "{sample}"
            / "contig_selection.log"
        )

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m mitopipeline.exec.select_mitochondrial_contig \
            --sample-id {wildcards.sample:q} \
            --assembly-fasta {input.assembly_fasta:q} \
            --top-hits {input.top_hits:q} \
            --output-fasta {output.fasta:q} \
            --log-file {params.log_file:q}

        test -s {output.fasta:q}
        touch {output.done:q}
        """