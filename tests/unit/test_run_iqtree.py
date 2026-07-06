"""test_run_iqtree.py

Unit tests for IQ-TREE execution.
"""

# Imports
from pathlib import Path
from types import SimpleNamespace

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from mitopipeline.exec import run_iqtree as iqtree_exec


class FakeLogger:
    """Minimal test logger."""

    def info(self, message):
        """Accept informational messages."""


def create_alignment(
        alignment_path: Path,
) -> None:
    """Create a seven-sequence test alignment."""
    records = [
        SeqRecord(
            Seq("ATGC--"),
            id="sample_001|assembled",
            description="",
        ),
        *[
            SeqRecord(
                Seq("ATGC--"),
                id=(
                    f"reference_{rank:02d}"
                    f"|NC_00000{rank}.1"
                    f"|Species_{rank}"
                ),
                description="",
            )
            for rank in range(1, 7)
        ],
    ]

    SeqIO.write(
        records,
        alignment_path,
        "fasta",
    )


def test_resolve_iqtree_executable(
        monkeypatch,
):
    """Confirm fallback executable detection works."""
    def fake_which(executable):
        if executable == "iqtree2":
            return "/test/bin/iqtree2"

        return None

    monkeypatch.setattr(
        iqtree_exec.shutil,
        "which",
        fake_which,
    )

    result = (
        iqtree_exec.resolve_iqtree_executable(
            "iqtree3"
        )
    )

    assert result == "/test/bin/iqtree2"


def test_run_iqtree(
        tmp_path: Path,
        monkeypatch,
):
    """Confirm IQ-TREE command and Newick output handling."""
    alignment_path = tmp_path / "aligned.fasta"
    output_prefix = tmp_path / "sample"
    output_newick = tmp_path / "sample.nwk"

    create_alignment(
        alignment_path
    )

    treefile_path = Path(
        f"{output_prefix}.treefile"
    )

    treefile_path.write_text(
        (
            "("
            "sample_001|assembled:0.1,"
            "reference_01|NC_000001.1|Species_1:0.1,"
            "reference_02|NC_000002.1|Species_2:0.1,"
            "reference_03|NC_000003.1|Species_3:0.1,"
            "reference_04|NC_000004.1|Species_4:0.1,"
            "reference_05|NC_000005.1|Species_5:0.1,"
            "reference_06|NC_000006.1|Species_6:0.1"
            ");"
        ),
        encoding="utf-8",
    )

    calls = {}

    monkeypatch.setattr(
        iqtree_exec,
        "resolve_iqtree_executable",
        lambda preferred: "/test/bin/iqtree3",
    )

    def fake_run(
            command,
            capture_output,
            text,
            check,
    ):
        calls["command"] = command

        return SimpleNamespace(
            returncode=0,
            stdout="IQ-TREE completed.",
            stderr="",
        )

    monkeypatch.setattr(
        iqtree_exec.subprocess,
        "run",
        fake_run,
    )

    iqtree_exec.run_iqtree(
        alignment_path=alignment_path,
        output_prefix=output_prefix,
        output_newick=output_newick,
        iqtree_bin="iqtree3",
        threads=4,
        sequence_type="DNA",
        model="MFP",
        ultrafast_bootstrap=1000,
        sh_alrt=1000,
        random_seed=12345,
        logger=FakeLogger(),
    )

    assert calls["command"] == [
        "/test/bin/iqtree3",
        "-s",
        str(alignment_path),
        "-st",
        "DNA",
        "-m",
        "MFP",
        "-B",
        "1000",
        "--alrt",
        "1000",
        "-T",
        "4",
        "--seed",
        "12345",
        "--prefix",
        str(output_prefix),
    ]

    assert output_newick.exists()