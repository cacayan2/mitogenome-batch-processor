"""mitos2_config.smk

Contains rules for setting up MITOS2 annotation dependencies.
"""

# Imports
from pathlib import Path


rule setup_mitos2:
    """Set up the MITOS2 Conda environment and reference data."""

    output:
        done=str(JOB_DIR / "setup" / "mitos2" / "mitos2.done")

    params:
        env_name=config["tools"]["mitos2"].get("conda_env", "mito-annotation"),
        env_file=str(Path(config["tools"]["mitos2"].get("env_file", "envs/annotation.yaml")).resolve()),
        refdir=str(Path(config["tools"]["mitos2"]["refdir"]).resolve()),
        refseqver=config["tools"]["mitos2"]["refseqver"],
        zenodo_record=config["tools"]["mitos2"].get("zenodo_record", "4284483"),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "setup" / "mitos2.log").resolve())

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.utils.setup_mitos2_env \
            --env-name {params.env_name} \
            --env-file {params.env_file} \
            --refseqver {params.refseqver} \
            --refdir {params.refdir} \
            --zenodo-record {params.zenodo_record} \
            --done-file {output.done} \
            --log-file {params.log_file}
        """