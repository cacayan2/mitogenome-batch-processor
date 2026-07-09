"""Unit tests for the BioSample metadata CLI."""

import json
from pathlib import Path
import sys

import pandas as pd

from mitopipeline.exec import generate_biosample_metadata


def test_main_writes_output(
        tmp_path: Path,
        monkeypatch,
):
    """CLI writes the requested BioSample metadata table."""
    manifest = tmp_path / "runtime_manifest.tsv"
    pd.DataFrame(
        [
            {
                "sample_id": "sample_001",
                "genus": "Lepomis",
                "species": "macrochirus",
            }
        ]
    ).to_csv(
        manifest,
        sep="\t",
        index=False,
    )

    output = tmp_path / "biosample_metadata.tsv"
    log_file = tmp_path / "biosample.log"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_biosample_metadata",
            "--runtime-manifest",
            str(manifest),
            "--output",
            str(output),
            "--defaults-json",
            json.dumps(
                {
                    "isolation_source": "eDNA water filter",
                    "collection_date": "2026-06",
                    "geo_loc_name": "USA: Illinois",
                }
            ),
            "--log-file",
            str(log_file),
        ],
    )

    assert generate_biosample_metadata.main() == 0
    assert output.exists()
