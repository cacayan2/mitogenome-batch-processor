"""Top BLAST-hit selection rule."""

from pathlib import Path


rule select_blast_hits:
    input:
        blast_results=str(
            JOB_DIR / "phylogeny" / "{sample}" / "blast.tsv"
        ),
        blast_done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "blast.done"
        )

    output:
        matches=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.tsv"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "top_hits.done"
        )

    params:
        maximum_matches=config["tools"]["blast"].get(
            "maximum_matches",
            6,
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "top_hits.log"
            ).resolve()
        )

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m mitopipeline.exec.parse_blast_hits \
            --sample-id {wildcards.sample} \
            --blast-results {input.blast_results:q} \
            --output-file {output.matches:q} \
            --maximum-matches {params.maximum_matches} \
            --log-file {params.log_file:q}

        test -e {output.matches:q}
        touch {output.done:q}
        """
