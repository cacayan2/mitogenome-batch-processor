"""blast.smk

Contains rules for validating mitochondrial genome assemblies with BLAST.
"""

# Imports
from pathlib import Path

def blast_database_input(config):
    """Return BLAST database setup dependency when enabled."""

    blast_config = config["tools"]["blast"]

    if blast_config.get("initialize_database", True):
        return str(
            JOB_DIR
            / "setup"
            / "blast"
            / "blast_database.done"
        )

    return []

def blast_optional_args(config):
    """Build optional BLAST command-line arguments.

    Args:
        config (dict): Pipeline configuration.

    Returns:
        str: Optional BLAST arguments.
    """
    # Extracting BLAST options from config.
    blast_config = config["tools"]["blast"]
    args = []

    # Creating dictionary of optional BLAST arguments.
    value_options = {
        "perc_identity": "--perc-identity",
        "query_coverage": "--query-coverage",
        "word_size": "--word-size",
    }

    # Adding optional BLAST arguments.
    for option_name, flag in value_options.items():
        value = blast_config.get(option_name)

        if value is not None:
            args.append(f"{flag} {value}")

    # Returning string of optional BLAST arguments.
    return " ".join(args)


rule blast_validation:
    """Run local BLAST validation on an assembled mitochondrial genome."""
    # Required arguments.
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
        database_done=blast_database_input(config)
    # Output arguments.
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
    # Parameter arguments.
    params:
        output_dir=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "blast"
            ).resolve()
        ),
        working_dir=str(Path.cwd()),
        database=str(
            Path(config["tools"]["blast"]["database"]).resolve()
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "blast"
                / "{sample}.log"
            ).resolve()
        ),
        task=config["tools"]["blast"].get(
            "task",
            "blastn",
        ),
        output_format=config["tools"]["blast"].get(
            "output_format",
            (
                "6 qseqid sseqid pident length mismatch gapopen "
                "qstart qend sstart send evalue bitscore qcovs "
                "staxids sscinames stitle"
            ),
        ),
        evalue=config["tools"]["blast"].get(
            "evalue",
            1e-5,
        ),
        max_target_seqs=config["tools"]["blast"].get(
            "max_target_seqs",
            10,
        ),
        max_hsps=config["tools"]["blast"].get(
            "max_hsps",
            1,
        ),
        optional_args=blast_optional_args(config)
    # Config arguments.
    threads:
        config["tools"]["blast"].get("threads", 4)
    # Snakemake arguments.
    conda:
        "../../envs/blast.yaml"
    # Snakemake commands.
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.run_blast \
            --sample-id {wildcards.sample} \
            --query-fasta {input.query_fasta} \
            --database {params.database} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --threads {threads} \
            --log-file {params.log_file} \
            --task {params.task} \
            --output-format "{params.output_format}" \
            --evalue {params.evalue} \
            --max-target-seqs {params.max_target_seqs} \
            --max-hsps {params.max_hsps} \
            {params.optional_args}

        touch {output.done}
        """