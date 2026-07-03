"""mitos2_config.smk

Contains rules for initializing MITOS2 reference data.
"""

# Imports
from pathlib import Path


rule setup_mitos2_reference_data:
    """Download and initialize MITOS2 reference data."""

    output:
        done=str(JOB_DIR / "setup" / "mitos2" / "mitos2_reference_data.done")

    params:
        refdir=str(Path(config["tools"]["mitos2"]["refdir"]).resolve()),
        refseqver=config["tools"]["mitos2"]["refseqver"],
        zenodo_record=config["tools"]["mitos2"].get("zenodo_record", "4284483"),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "setup" / "mitos2_reference_data.log").resolve()),
        working_dir=str(Path.cwd())

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.utils.setup_mitos2_reference_data \
            --refseqver {params.refseqver} \
            --refdir {params.refdir} \
            --zenodo-record {params.zenodo_record} \
            --done-file {output.done} \
            --log-file {params.log_file}
        """