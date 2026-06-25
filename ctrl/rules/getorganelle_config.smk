"""getorganelle_config.smk

Contains rules for GetOrganelle database initialization.
"""

# Imports
from pathlib import Path

rule getorganelle_config:
    """initialize GetOrganelle reference databases."""

    # Specifying output done file.
    output:
        done = str(JOB_DIR / "setup" / "getorganelle" / "{database_type}.done")

    # Specifying params.
    params:
        log_file = str(JOB_DIR / "logs" / "setup" / "getorganelle_config.{database_type}.log")

    # Specifying conda environment.
    conda:
        "../../envs/assembly.yaml"

    # Shell script for running getorganelle database setup.
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.utils.setup_getorganelle_database \
            --database-type {wildcards.database_type} \
            --done-file {output.done} \
            --log-file {params.log_file}
        """