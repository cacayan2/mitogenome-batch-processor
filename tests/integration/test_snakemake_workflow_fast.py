from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow

def test_snakemake_dry_run():
    """Integration test confirming Snakemake can build the workflow DAG."""

    # Defining fixture output directory.
    output_dir = Path("tests/fixtures/outputs/test_job")

    # Removing previous test outputs.
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Running Snakemake dry run.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config.yaml",
                "--dry-run",
                "--cores",
                "1",
            ],
            capture_output=True,
            text=True,
        )

        # Assert statements.
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Building DAG of jobs" in result.stdout
        assert "rule qc_raw" in result.stdout
        assert "rule qc_trimmed" in result.stdout
        assert "rule assembly" in result.stdout
        assert "rule annotation" in result.stdout
        assert "rule circular_genome_map" in result.stdout
        assert "rule blast" in result.stdout
        assert "rule select_blast_hits" in result.stdout
        assert "rule generate_alignment_dataset" in result.stdout
        assert "rule align_phylogeny_dataset" in result.stdout
        assert "rule infer_phylogeny" in result.stdout
        assert "rule render_phylogenetic_tree" in result.stdout
        assert "rule reporting" in result.stdout
        assert "rule circular_genome_map" in result.stdout
        assert "rule sra_metadata" in result.stdout
        assert "rule biosample_metadata" in result.stdout
        
    finally:
        # Cleanup.
        if output_dir.exists():
            shutil.rmtree(output_dir)