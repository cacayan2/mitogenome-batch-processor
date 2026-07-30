"""
04-getorganelle_config.smk

Rules for creating the reference database for GetOrganelle.
"""

# Imports
from pathlib import Path

rule getorganelle_config:
    output:
        """
        Note that there is no input, but simply an output.
        GetOrganelle depends on this database, so using the .done file
        generated, Snakemake will ensure that this rule is run first.

        Args:
            done: The done file generated once the database is generated.
        """
        done = str(JOB_DIR / "setup" / "getorganelle" / "{database_type}.done")
    params:
        """
        The only param passed here is the log file.

        Args:
            log_file: The location of the log file for this portion of the pipeline.
        """
        log_file = str(JOB_DIR / "logs" / "setup" / "getorganelle_config.{database_type}.log")
    conda:
        "../../envs/assembly.yaml"
    shell:
        """
        python -m mitopipeline.utils.setup_getorganelle_database \
            --database-type {wildcards.database_type} \
            --log-file {params.log_file:q}
        touch {output.done:q}
        """