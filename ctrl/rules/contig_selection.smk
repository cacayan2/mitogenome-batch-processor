"""Mitochondrial assembly assessment and primary-contig selection rule."""

from pathlib import Path


ASSESSMENT_CONFIG = config.get("assembly_assessment", {})


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
        fragments=str(
            JOB_DIR / "assembly" / "{sample}" / "mitochondrial_fragments.fasta"
        ),
        assessment=str(
            JOB_DIR / "assembly" / "{sample}" / "assembly_assessment.json"
        ),
        done=str(
            JOB_DIR / "assembly" / "{sample}" / "selection.done"
        )

    params:
        complete_min_length=ASSESSMENT_CONFIG.get(
            "complete_min_length",
            14000,
        ),
        complete_max_length=ASSESSMENT_CONFIG.get(
            "complete_max_length",
            22000,
        ),
        minimum_fragment_length=ASSESSMENT_CONFIG.get(
            "minimum_fragment_length",
            200,
        ),
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
        set -euo pipefail

        python -m mitopipeline.exec.select_mitochondrial_contig \
            --sample-id {wildcards.sample:q} \
            --assembly-fasta {input.assembly_fasta:q} \
            --top-hits {input.top_hits:q} \
            --output-fasta {output.fasta:q} \
            --fragments-fasta {output.fragments:q} \
            --assessment-json {output.assessment:q} \
            --complete-min-length {params.complete_min_length} \
            --complete-max-length {params.complete_max_length} \
            --minimum-fragment-length {params.minimum_fragment_length} \
            --log-file {params.log_file:q}

        test -s {output.fasta:q}
        test -s {output.fragments:q}
        test -s {output.assessment:q}
        touch {output.done:q}
        """
