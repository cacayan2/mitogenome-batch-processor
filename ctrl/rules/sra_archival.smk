"""Generate a reviewable NCBI SRA metadata table."""

import json
from pathlib import Path


SRA_CONFIG = config.get(
    "archival",
    {},
).get(
    "sra",
    {},
)


rule sra_metadata:
    """Write one SRA metadata row per raw sequencing sample."""

    input:
        runtime_manifest=str(
            RUNTIME_MANIFEST_PATH
        )

    output:
        metadata=str(
            JOB_DIR
            / "submission"
            / "sra"
            / "sra_metadata.tsv"
        )

    params:
        defaults_json=lambda wildcards: json.dumps(
            SRA_CONFIG,
            separators=(",", ":"),
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "archival"
                / "sra_metadata.log"
            ).resolve()
        )

    shell:
        r"""

        python -m mitopipeline.exec.generate_sra_metadata \
            --runtime-manifest {input.runtime_manifest:q} \
            --output {output.metadata:q} \
            --defaults-json '{params.defaults_json}' \
            --log-file {params.log_file:q}
        """
