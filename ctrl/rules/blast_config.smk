"""blast_config.smk

Contains rules for setting up the local BLAST reference database.
"""

# Imports
from pathlib import Path

def blast_database_optional_args(config):
    """Build optional arguments for BLAST database setup.
    
    Args:
        config (dict): Configuration dictionary.
    
    Returns:
        str: String of optional arguments.
    """
    # Extracting BLAST options from config.
    blast_config = config["tools"]["blast"]
    args = []

    # Adding optional arguments.
    if blast_config.get("parse_seqids", False):
        args.append("--parse-seqids")

    if blast_config.get("overwrite_database", False):
        args.append("--overwrite")

    # Returning string of optional arguments.
    return " ".join(args)

rule setup_blast_database:
    """Build and validate the local nucleotide BLAST database."""

    # Required arguments.
    input:
        reference_fasta=lambda wildcards: str(
            Path(config["tools"]["blast"]["reference_fasta"]).resolve()
        )

    # Optional arguments.
    output:
        done=str(JOB_DIR / "setup" / "blast" / "blast_database.done")

    # Specifying params.
    params:
        database_prefix=str(
            Path(config["tools"]["blast"]["database"]).resolve()
        ),
        database_title=config["tools"]["blast"].get(
            "database_title",
            "mitopipeline mitochondrial reference database",
        ),
        metadata_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "setup"
                / "blast"
                / "blast_database.metadata.json"
            ).resolve()
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "setup"
                / "blast_database.log"
            ).resolve()
        ),
        optional_args=blast_database_optional_args(config),

    # Specifying conda environment.
    conda:
        "../../envs/blast.yaml"

    # Shell script for running BLAST database setup.
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.utils.setup_blast_database \
            --input-fasta {input.reference_fasta} \
            --database-prefix {params.database_prefix} \
            --database-title "{params.database_title}" \
            --metadata-file {params.metadata_file} \
            --done-file {output.done} \
            --log-file {params.log_file} \
            {params.optional_args}
        """