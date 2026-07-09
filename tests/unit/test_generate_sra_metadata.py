"""Unit tests for the SRA metadata CLI."""

import json
from pathlib import Path
import sys

import pandas as pd

from mitopipeline.exec import generate_sra_metadata


def test_main_writes_output(
        tmp_path: Path,
        monkeypatch,
):
    """CLI writes the requested SRA metadata table."""
    r1 = tmp_path / "R1.fastq.gz"
    r2 = tmp_path / "R2.fastq.gz"
    r1.touch()
    r2.touch()

    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "r1": str(r1),
                "r2": str(r2),
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    output = tmp_path / "sra_metadata.tsv"
    log_file = tmp_path / "sra.log"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_sra_metadata",
            "--runtime-manifest",
            str(manifest),
            "--output",
            str(output),
            "--defaults-json",
            json.dumps(
                {
                    "library_strategy": "WGS",
                    "library_source": "GENOMIC",
                    "library_selection": "RANDOM",
                    "platform": "ILLUMINA",
                    "instrument_model": "Illumina NovaSeq 6000",
                }
            ),
            "--log-file",
            str(log_file),
        ],
    )

    assert generate_sra_metadata.main() == 0
    assert output.exists()
