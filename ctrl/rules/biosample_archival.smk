"""Generate a reviewable NCBI BioSample metadata table."""

import json
from pathlib import Path


BIOSAMPLE_CONFIG = config.get(
    "archival",
    {},
).get(
    "biosample",
    {},
)


rule biosample_metadata:
    """Write one BioSample metadata row per biological sample."""

    input:
        runtime_manifest=str(
            RUNTIME_MANIFEST_PATH
        )

    output:
        metadata=str(
            JOB_DIR
            / "submission"
            / "biosample"
            / "biosample_metadata.tsv"
        )

    params:
        defaults_json=lambda wildcards: json.dumps(
            BIOSAMPLE_CONFIG,
            separators=(",", ":"),
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "archival"
                / "biosample_metadata.log"
            ).resolve()
        )

    shell:
        r"""
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.generate_biosample_metadata \
            --runtime-manifest {input.runtime_manifest:q} \
            --output {output.metadata:q} \
            --defaults-json '{params.defaults_json}' \
            --log-file {params.log_file:q}
        """
