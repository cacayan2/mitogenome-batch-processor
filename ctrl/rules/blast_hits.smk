"""blast_hits.smk

Contains rules for selecting top BLAST matches.
"""

# Imports
from pathlib import Path


rule select_blast_hits:
    """Select the top six unique BLAST matches for each sample.
    
    Input:
        blast_results: Path to BLAST TSV results.
        blast_done: Path to BLAST done file.
    
    Output:
        matches: Path to selected-hit TSV output.
        done: Path to selected-hit done file.
    """
    # Inputs
    input:
        blast_results=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.blast.tsv"
        ),
        blast_done=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.blast.done"
        )
    # Outputs
    output:
        matches=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.top_hits.tsv"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.top_hits.done"
        )
    # Parameters
    params:
        maximum_matches=config["tools"]["blast"].get(
            "maximum_matches",
            6,
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "blast_hits"
                / "{sample}.log"
            ).resolve()
        )
    # Conda environment
    conda:
        "../../envs/mitopipeline.yaml"
    # Shell script
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.parse_blast_hits \
            --sample-id {wildcards.sample} \
            --blast-results {input.blast_results} \
            --output-file {output.matches} \
            --maximum-matches {params.maximum_matches} \
            --log-file {params.log_file}

        touch {output.done}
        """