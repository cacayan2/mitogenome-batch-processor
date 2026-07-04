"""blast_config.smk

Set up a local BLAST database using fixed switchboard configuration.
"""

# Imports
from pathlib import Path

from mitopipeline.config.blast_config import BlastConfig


BLAST_CONFIG = BlastConfig.from_mapping(
    config["tools"]["blast"]
)


def blast_setup_optional_args():
    """Build optional database setup arguments."""
    args = []

    if BLAST_CONFIG.parse_seqids:
        args.append("--parse-seqids")

    if BLAST_CONFIG.overwrite_database:
        args.append("--overwrite")

    return " ".join(args)


def blast_reference_input():
    """Return reference FASTA dependency for custom FASTA mode."""
    if BLAST_CONFIG.uses_reference_fasta:
        return str(
            BLAST_CONFIG.reference_fasta.resolve()
        )

    return []


rule setup_blast_database:
    """Build or download the selected local BLAST database.
    
    Input:
        reference: Path to reference FASTA file.
    
    Output:
        done: Path to BLAST database setup done file.
    """
    # Inputs
    input:
        reference=blast_reference_input()
    # Outputs
    output:
        done=str(
            JOB_DIR
            / "setup"
            / "blast"
            / "blast_database.done"
        )
    # Specifying params.
    params:
        database_source=BLAST_CONFIG.database_source,
        database_name=BLAST_CONFIG.database_name,
        database_dir=str(
            BLAST_CONFIG.database_dir.resolve()
        ),
        reference_fasta=str(
            BLAST_CONFIG.reference_fasta.resolve()
        ),
        database_title=BLAST_CONFIG.database_title,
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
        optional_args=blast_setup_optional_args()
    # Specifying conda environment.
    conda:
        "../../envs/blast.yaml"
    # Shell script for running BLAST database setup.
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.utils.setup_blast_database \
            --database-source {params.database_source} \
            --database-name {params.database_name} \
            --database-dir {params.database_dir} \
            --reference-fasta {params.reference_fasta} \
            --database-title "{params.database_title}" \
            --metadata-file {params.metadata_file} \
            --done-file {output.done} \
            --log-file {params.log_file} \
            {params.optional_args}
        """