"""Set up MITOS2 and its reference data."""

from pathlib import Path

MITOS2_CONFIG = config["tools"]["mitos2"]
MITOS2_REFDIR = Path(MITOS2_CONFIG["refdir"]).resolve()
MITOS2_REFSEQVER = MITOS2_CONFIG["refseqver"]
MITOS2_READY_FILE = MITOS2_REFDIR / MITOS2_REFSEQVER / ".mitopipeline_reference_ready"

rule setup_mitos2:
    output:
        done=str(JOB_DIR / "setup" / "mitos2" / "mitos2.done"),
        reference_ready=str(MITOS2_READY_FILE)

    params:
        env_name=MITOS2_CONFIG.get("conda_env", "mito-annotation"),
        env_file=str(Path(MITOS2_CONFIG.get("env_file", "envs/annotation.yaml")).resolve()),
        refdir=str(MITOS2_REFDIR),
        refseqver=MITOS2_REFSEQVER,
        zenodo_record=MITOS2_CONFIG.get("zenodo_record", "4284483"),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "setup" / "mitos2.log").resolve())

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m mitopipeline.utils.setup_mitos2_env \
            --env-name {params.env_name:q} \
            --env-file {params.env_file:q} \
            --refseqver {params.refseqver:q} \
            --refdir {params.refdir:q} \
            --zenodo-record {params.zenodo_record:q} \
            --reference-ready-file {output.reference_ready:q} \
            --done-file {output.done:q} \
            --log-file {params.log_file:q}

        test -s {output.reference_ready:q}
        test -s {output.done:q}
        """
