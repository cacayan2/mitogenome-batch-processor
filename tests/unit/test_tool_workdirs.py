"""Tests for sample-isolated tool work directory layouts."""

from pathlib import Path

from mitopipeline.io.tool_workdirs import SampleWorkLayout, unique_file


def test_sample_work_layout_paths(tmp_path: Path):
    layout = SampleWorkLayout(stage_dir=tmp_path / "assembly", sample_id="sample_001")
    assert layout.sample_work_dir == tmp_path / "assembly" / "work" / "sample_001"
    assert layout.normalized_output(".fasta") == tmp_path / "assembly" / "sample_001.fasta"


def test_prepare_work_dir_overwrite(tmp_path: Path):
    layout = SampleWorkLayout(stage_dir=tmp_path / "assembly", sample_id="sample_001")
    work_dir = layout.prepare_work_dir()
    stale_file = work_dir / "old.txt"
    stale_file.write_text("stale", encoding="utf-8")
    layout.prepare_work_dir(overwrite=True)
    assert work_dir.exists()
    assert not stale_file.exists()


def test_unique_file(tmp_path: Path):
    target = tmp_path / "a.path_sequence.fasta"
    target.write_text(">x\nACGT\n", encoding="utf-8")
    assert unique_file(tmp_path, "*.path_sequence.fasta", "path sequence") == target
