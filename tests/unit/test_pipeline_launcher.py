"""test_pipeline_launcher.py

Unit tests for the mitopipeline launcher.
"""

# Imports
from pathlib import Path
import subprocess
import yaml
import pytest

from mitopipeline.launcher.pipeline_launcher import (
    load_config,
    discover_fastq_pairs,
    write_sample_manifest,
    prepare_runtime_manifest,
    write_runtime_config,
    run_snakemake,
)


class DummyJob:
    """Minimal PipelineJob-like object for launcher unit tests."""

    def __init__(self, job_dir: Path, parent_dir: Path):
        self.job_id = "test_job"
        self.job_dir = job_dir
        self.parent_dir = parent_dir
        self.job_logger = DummyLogger()


class DummyLogger:
    """Minimal logger-like object for launcher unit tests."""

    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def exception(self, message):
        pass


def write_fastq(path: Path) -> None:
    """Write a minimal non-empty FASTQ file."""

    path.write_text(
        "@read1\n"
        "ACGT\n"
        "+\n"
        "!!!!\n",
        encoding="utf-8",
    )


def test_load_config_reads_yaml(tmp_path):
    """Test that load_config reads a YAML file."""

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "output_root: outputs\n"
        "input_dir: data/raw\n"
        "manifest: null\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["output_root"] == "outputs"
    assert config["input_dir"] == "data/raw"
    assert config["manifest"] is None


def test_load_config_missing_file_raises(tmp_path):
    """Test that load_config raises for a missing file."""

    missing_config = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(missing_config)


def test_load_config_empty_file_raises(tmp_path):
    """Test that load_config raises for an empty YAML file."""

    config_path = tmp_path / "empty.yaml"
    config_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(config_path)


def test_discover_fastq_pairs_with_r1_r2_names(tmp_path):
    """Test FASTQ discovery using _R1/_R2 naming."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    r1 = input_dir / "sample_001_R1.fastq.gz"
    r2 = input_dir / "sample_001_R2.fastq.gz"

    write_fastq(r1)
    write_fastq(r2)

    job = DummyJob(job_dir=tmp_path / "job", parent_dir=tmp_path)

    records = discover_fastq_pairs(input_dir, job)

    assert len(records) == 1
    assert records[0]["sample_id"] == "sample_001"
    assert records[0]["r1"] == str(r1)
    assert records[0]["r2"] == str(r2)
    assert records[0]["source"] == "discovered_fastq"


def test_discover_fastq_pairs_with_1_2_names(tmp_path):
    """Test FASTQ discovery using _1/_2 naming."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    r1 = input_dir / "sample_001_1.fastq.gz"
    r2 = input_dir / "sample_001_2.fastq.gz"

    write_fastq(r1)
    write_fastq(r2)

    job = DummyJob(job_dir=tmp_path / "job", parent_dir=tmp_path)

    records = discover_fastq_pairs(input_dir, job)

    assert len(records) == 1
    assert records[0]["sample_id"] == "sample_001"
    assert records[0]["r1"] == str(r1)
    assert records[0]["r2"] == str(r2)


def test_discover_fastq_pairs_missing_r2_raises(tmp_path):
    """Test FASTQ discovery raises when R2 is missing."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    write_fastq(input_dir / "sample_001_R1.fastq.gz")

    job = DummyJob(job_dir=tmp_path / "job", parent_dir=tmp_path)

    with pytest.raises(ValueError):
        discover_fastq_pairs(input_dir, job)


def test_discover_fastq_pairs_no_fastqs_raises(tmp_path):
    """Test FASTQ discovery raises when no FASTQs exist."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    job = DummyJob(job_dir=tmp_path / "job", parent_dir=tmp_path)

    with pytest.raises(FileNotFoundError):
        discover_fastq_pairs(input_dir, job)


def test_write_sample_manifest(tmp_path):
    """Test writing sample records to a manifest."""

    manifest_path = tmp_path / "validated_samples.tsv"

    records = [
        {
            "sample_id": "sample_001",
            "r1": "sample_001_R1.fastq.gz",
            "r2": "sample_001_R2.fastq.gz",
            "genus": "Danio",
            "species": "rerio",
            "source": "test",
        }
    ]

    job = DummyJob(job_dir=tmp_path / "job", parent_dir=tmp_path)

    write_sample_manifest(manifest_path, records, job)

    text = manifest_path.read_text(encoding="utf-8")

    assert "sample_id\tr1\tr2\tgenus\tspecies\tsource" in text
    assert "sample_001\tsample_001_R1.fastq.gz\tsample_001_R2.fastq.gz\tDanio\trerio\ttest" in text


def test_prepare_runtime_manifest_from_existing_manifest(tmp_path):
    """Test preparing runtime manifest from an existing manifest."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    r1 = input_dir / "sample_001_R1.fastq.gz"
    r2 = input_dir / "sample_001_R2.fastq.gz"

    write_fastq(r1)
    write_fastq(r2)

    manifest_path = tmp_path / "samples.tsv"
    manifest_path.write_text(
        "sample_id\tr1\tr2\tgenus\tspecies\tsource\n"
        f"sample_001\t{r1}\t{r2}\tDanio\trerio\ttest\n",
        encoding="utf-8",
    )

    job_dir = tmp_path / "outputs" / "test_job"
    job_dir.mkdir(parents=True)

    job = DummyJob(job_dir=job_dir, parent_dir=tmp_path / "outputs")

    config = {
        "manifest": str(manifest_path),
        "input_dir": str(input_dir),
    }

    runtime_manifest = prepare_runtime_manifest(config, job)

    assert runtime_manifest == job_dir / "validated_samples.tsv"
    assert runtime_manifest.exists()
    assert "sample_001" in runtime_manifest.read_text(encoding="utf-8")


def test_prepare_runtime_manifest_from_discovered_fastqs(tmp_path):
    """Test preparing runtime manifest by discovering FASTQ files."""

    input_dir = tmp_path / "fastq"
    input_dir.mkdir()

    r1 = input_dir / "sample_001_R1.fastq.gz"
    r2 = input_dir / "sample_001_R2.fastq.gz"

    write_fastq(r1)
    write_fastq(r2)

    job_dir = tmp_path / "outputs" / "test_job"
    job_dir.mkdir(parents=True)

    job = DummyJob(job_dir=job_dir, parent_dir=tmp_path / "outputs")

    config = {
        "manifest": None,
        "input_dir": str(input_dir),
    }

    runtime_manifest = prepare_runtime_manifest(config, job)

    assert runtime_manifest == job_dir / "validated_samples.tsv"
    assert runtime_manifest.exists()

    text = runtime_manifest.read_text(encoding="utf-8")

    assert "sample_001" in text
    assert str(r1) in text
    assert str(r2) in text


def test_write_runtime_config(tmp_path):
    """Test writing runtime config."""

    job_dir = tmp_path / "outputs" / "test_job"
    job_dir.mkdir(parents=True)

    job = DummyJob(job_dir=job_dir, parent_dir=tmp_path / "outputs")

    runtime_manifest = job_dir / "validated_samples.tsv"
    runtime_manifest.write_text("sample_id\tr1\tr2\n", encoding="utf-8")

    config = {
        "output_root": "old_outputs",
        "manifest": "old_manifest.tsv",
        "input_dir": "data/raw",
        "stages": {"qc_raw": True},
    }

    runtime_config_path = write_runtime_config(config, job, runtime_manifest)

    assert runtime_config_path.exists()

    runtime_config = yaml.safe_load(runtime_config_path.read_text(encoding="utf-8"))

    assert runtime_config["job_id"] == "test_job"
    assert runtime_config["manifest"] == str(runtime_manifest)
    assert runtime_config["output_root"] == str(job.parent_dir)
    assert runtime_config["input_dir"] == "data/raw"
    assert runtime_config["stages"]["qc_raw"] is True


def test_run_snakemake_builds_expected_command(monkeypatch, tmp_path):
    """Test run_snakemake builds and runs the expected command."""

    calls = {}

    def fake_run(command, capture_output, text):
        calls["command"] = command
        calls["capture_output"] = capture_output
        calls["text"] = text

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    logger = DummyLogger()

    result = run_snakemake(
        snakefile=Path("ctrl/Snakefile"),
        runtime_config=tmp_path / "runtime_config.yaml",
        cores=4,
        use_conda=True,
        logger=logger,
    )

    assert result.returncode == 0
    assert calls["command"] == [
        "snakemake",
        "-s",
        "ctrl/Snakefile",
        "--configfile",
        str(tmp_path / "runtime_config.yaml"),
        "--cores",
        "4",
        "--use-conda",
    ]
    assert calls["capture_output"] is True
    assert calls["text"] is True