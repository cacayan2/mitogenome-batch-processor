"""blast.smk

Run local or remote BLAST validation.
"""

# Imports
from pathlib import Path

from mitopipeline.config.blast_config import BlastConfig


BLAST_CONFIG = BlastConfig.from_mapping(
    config["tools"]["blast"]
)

def blast_max_hsps_arg():
    """Return max-HSP argument when configured."""
    if BLAST_CONFIG.max_hsps is None:
        return ""

    return f"--max-hsps {BLAST_CONFIG.max_hsps}"

def blast_database_dependency():
    """Return database setup dependency when required."""
    if BLAST_CONFIG.requires_database_setup:
        return str(
            JOB_DIR
            / "setup"
            / "blast"
            / "blast_database.done"
        )

    return []


def blast_optional_args():
    """Build optional blastn arguments."""
    args = []

    value_options = {
        BLAST_CONFIG.perc_identity: "--perc-identity",
        BLAST_CONFIG.query_coverage: "--query-coverage",
        BLAST_CONFIG.word_size: "--word-size",
    }

    for value, flag in value_options.items():
        if value is not None:
            args.append(
                f"{flag} {value}"
            )

    return " ".join(args)


rule blast_validation:
    """Run selected local or remote BLAST mode.
    
    Inputs:
        - query_fasta: Assembly FASTA file.
        - assembly_done: Assembly validation done file.
        - database_done: BLAST database setup done file.

    Outputs:
        - results: BLAST results file.
        - done: BLAST validation done file.
    """
    # Inputs
    input:
        query_fasta=str(
            JOB_DIR
            / "assembly"
            / "{sample}.fasta"
        ),
        assembly_done=str(
            JOB_DIR
            / "assembly"
            / "{sample}.assembly.done"
        ),
        database_done=blast_database_dependency()
    # Outputs
    output:
        results=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.blast.tsv"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "blast"
            / "{sample}.blast.done"
        )
    # Parameters
    params:
        mode=BLAST_CONFIG.mode,
        database=BLAST_CONFIG.database_argument,
        output_dir=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "blast"
            ).resolve()
        ),
        working_dir=str(Path.cwd()),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "blast"
                / "{sample}.log"
            ).resolve()
        ),
        task=BLAST_CONFIG.task,
        output_format=BLAST_CONFIG.output_format,
        evalue=BLAST_CONFIG.evalue,
        max_target_seqs=BLAST_CONFIG.max_target_seqs,
        max_hsps_arg=blast_max_hsps_arg(),
        optional_args=blast_optional_args()
    # Thread specification.
    threads:
        BLAST_CONFIG.threads
    # Environment
    conda:
        "../../envs/blast.yaml"
    # Run BLAST
    shell:
        """

        python -m mitopipeline.exec.run_blast \
            --sample-id {wildcards.sample} \
            --query-fasta {input.query_fasta} \
            --database {params.database} \
            --mode {params.mode} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --threads {threads} \
            --log-file {params.log_file} \
            --task {params.task} \
            --output-format "{params.output_format}" \
            --evalue {params.evalue} \
            --max-target-seqs {params.max_target_seqs} \
            {params.max_hsps_arg} \
            {params.optional_args}

        touch {output.done}
        """