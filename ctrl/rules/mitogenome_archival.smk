"""Prepare assembled mitogenomes for NCBI/GenBank archival."""

import json
from pathlib import Path


MITOGENOME_ARCHIVAL_CONFIG = config.get(
    "archival",
    {},
).get(
    "mitogenome",
    {},
)


rule mitogenome_submission:
    """Collect assembly FASTA and MITOS2 annotation outputs."""

    input:
        runtime_manifest=str(
            RUNTIME_MANIFEST_PATH
        )

    output:
        metadata=str(
            JOB_DIR
            / "submission"
            / "mitogenomes"
            / "mitogenome_metadata.tsv"
        )

    params:
        output_directory=str(
            JOB_DIR
            / "submission"
            / "mitogenomes"
        ),
        defaults_json=lambda wildcards: json.dumps(
            MITOGENOME_ARCHIVAL_CONFIG,
            separators=(",", ":"),
        ),
        mode=MITOGENOME_ARCHIVAL_CONFIG.get(
            "file_mode",
            "copy",
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "archival"
                / "mitogenome_submission.log"
            ).resolve()
        )

    shell:
        r"""
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.prepare_mitogenome_submission \
            --runtime-manifest {input.runtime_manifest:q} \
            --job-directory {JOB_DIR:q} \
            --output-directory {params.output_directory:q} \
            --metadata-output {output.metadata:q} \
            --defaults-json '{params.defaults_json}' \
            --mode {params.mode:q} \
            --log-file {params.log_file:q}
        """
