"""test_mitos2_exec.py

Integration tests for the MITOS2 execution layer through Snakemake.
"""

# Imports
from pathlib import Path
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.slow


def test_mitos2_exec_layer_through_snakemake_real_assembly():
    """Integration test confirming Snakemake executes MITOS2 on existing assembly output."""

    # Defining test paths.
    sample_id = "common_carp_001"
    output_dir = Path("tests/fixtures/outputs/test_job")
    assembly_fasta = output_dir / "assembly" / f"{sample_id}.fasta"
    assembly_done = output_dir / "assembly" / f"{sample_id}.assembly.done"
    annotation_dir = output_dir / "annotation" / sample_id
    log_file = output_dir / "logs" / "annotation" / f"{sample_id}.log"
    target = output_dir / "annotation" / f"{sample_id}.annotation.done"

    # Removing previous annotation outputs only.
    if annotation_dir.exists():
        shutil.rmtree(annotation_dir)

    if target.exists():
        target.unlink()

    try:
        # Confirming this test does not need to rerun assembly.
        assert assembly_fasta.exists()
        assert assembly_done.exists()

        # Running the MITOS2 annotation rule through Snakemake.
        result = subprocess.run(
            [
                "snakemake",
                "-s",
                "ctrl/Snakefile",
                "--configfile",
                "tests/fixtures/config/config_mitos2_real.yaml",
                "--use-conda",
                "--cores",
                "4",
                str(target),
            ],
            capture_output=True,
            text=True,
        )

        # Assert statements.
        assert result.returncode == 0, result.stdout + result.stderr
        assert target.exists()
        assert log_file.exists()
        assert annotation_dir.exists()

        # Deterministic MITOS2 output assertions.
        assert (annotation_dir / "result.bed").exists()
        assert (annotation_dir / "result.faa").exists()
        assert (annotation_dir / "result.fas").exists()
        assert (annotation_dir / "result.geneorder").exists()
        assert (annotation_dir / "result.gff").exists()
        assert (annotation_dir / "result.mitos").exists()
        assert (annotation_dir / "result.seq").exists()
        assert (annotation_dir / "stst.dat").exists()

        # Intermediate directory assertions.
        assert (annotation_dir / "blast").exists()
        assert (annotation_dir / "blast" / "prot").exists()
        assert (annotation_dir / "blast" / "nuc").exists()
        assert (annotation_dir / "mitfi-global").exists()

    finally:
        # Leave outputs for inspection while MITOS2 integration stabilizes.
        pass