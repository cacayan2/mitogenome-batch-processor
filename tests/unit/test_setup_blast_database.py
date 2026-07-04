"""test_setup_blast_database.py

Unit tests for NCBI and custom FASTA BLAST database setup.
"""

# Imports
import json
from pathlib import Path
from types import SimpleNamespace

from mitopipeline.utils import setup_blast_database


class DummyLogger:
    """Minimal test logger."""

    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def exception(self, message):
        pass


def write_file(
    path: Path,
    contents: str = "test\n",
) -> None:
    """Write test file."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        contents,
        encoding="utf-8",
    )


def test_database_files_support_multivolume_database(
    tmp_path,
):
    """Test numbered NCBI database volumes are discovered."""
    prefix = (
        tmp_path
        / "blast"
        / "refseq_genomic"
    )

    write_file(
        Path(f"{prefix}.00.nhr")
    )
    write_file(
        Path(f"{prefix}.00.nin")
    )
    write_file(
        Path(f"{prefix}.00.nsq")
    )

    files = setup_blast_database.database_files(
        prefix
    )

    assert Path(f"{prefix}.00.nhr") in files
    assert Path(f"{prefix}.00.nin") in files
    assert Path(f"{prefix}.00.nsq") in files


def test_validate_database_uses_blastdbcmd(
    tmp_path,
    monkeypatch,
):
    """Test database validation uses blastdbcmd."""
    prefix = (
        tmp_path
        / "blast"
        / "refseq_genomic"
    )
    captured = {}

    def fake_run_command(
        command,
        logger,
        cwd=None,
    ):
        captured["command"] = command

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        setup_blast_database,
        "run_command",
        fake_run_command,
    )

    assert setup_blast_database.validate_database(
        prefix,
        DummyLogger(),
    )

    assert captured["command"] == [
        "blastdbcmd",
        "-db",
        str(prefix),
        "-dbtype",
        "nucl",
        "-info",
    ]


def test_download_ncbi_database_uses_database_name(
    tmp_path,
    monkeypatch,
):
    """Test NCBI downloader uses switchboard database_name."""
    captured = {}

    def fake_run_command(
        command,
        logger,
        cwd=None,
    ):
        captured["command"] = command
        captured["cwd"] = cwd

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        setup_blast_database,
        "run_command",
        fake_run_command,
    )

    database_dir = tmp_path / "blast"

    result = setup_blast_database.download_ncbi_database(
        database_name="refseq_genomic",
        database_dir=database_dir,
        logger=DummyLogger(),
    )

    assert result == 0
    assert captured["command"] == [
        "update_blastdb.pl",
        "--decompress",
        "refseq_genomic",
    ]
    assert captured["cwd"] == database_dir


def test_reference_fasta_validation(
    tmp_path,
):
    """Test valid FASTA is accepted."""
    reference_fasta = (
        tmp_path
        / "references.fasta"
    )

    write_file(
        reference_fasta,
        ">reference\nATGC\n",
    )

    assert (
        setup_blast_database.validate_reference_fasta(
            reference_fasta,
            DummyLogger(),
        )
        is True
    )


def test_ncbi_setup_skips_valid_database(
    tmp_path,
    monkeypatch,
):
    """Test existing valid NCBI database is reused."""
    database_dir = tmp_path / "blast"
    database_prefix = (
        database_dir
        / "refseq_genomic"
    )
    done_file = tmp_path / "blast.done"

    monkeypatch.setattr(
        setup_blast_database,
        "validate_database",
        lambda prefix, logger: True,
    )

    called = {"download": False}

    def fake_download(**kwargs):
        called["download"] = True
        return 0

    monkeypatch.setattr(
        setup_blast_database,
        "download_ncbi_database",
        fake_download,
    )

    result = setup_blast_database.setup_ncbi_database(
        database_name="refseq_genomic",
        database_prefix=database_prefix,
        database_dir=database_dir,
        overwrite=False,
        metadata_file=tmp_path / "metadata.json",
        done_file=done_file,
        logger=DummyLogger(),
    )

    assert result == 0
    assert called["download"] is False
    assert done_file.exists()


def test_ncbi_setup_downloads_missing_database(
    tmp_path,
    monkeypatch,
):
    """Test absent NCBI database is downloaded."""
    validation_results = iter([
        False,
        True,
    ])

    monkeypatch.setattr(
        setup_blast_database,
        "validate_database",
        lambda prefix, logger: next(
            validation_results
        ),
    )
    monkeypatch.setattr(
        setup_blast_database,
        "download_ncbi_database",
        lambda **kwargs: 0,
    )

    database_dir = tmp_path / "blast"
    database_prefix = (
        database_dir
        / "refseq_genomic"
    )
    metadata_file = tmp_path / "metadata.json"
    done_file = tmp_path / "blast.done"

    result = setup_blast_database.setup_ncbi_database(
        database_name="refseq_genomic",
        database_prefix=database_prefix,
        database_dir=database_dir,
        overwrite=False,
        metadata_file=metadata_file,
        done_file=done_file,
        logger=DummyLogger(),
    )

    assert result == 0
    assert metadata_file.exists()
    assert done_file.exists()

    metadata = json.loads(
        metadata_file.read_text(
            encoding="utf-8",
        )
    )

    assert metadata["database_source"] == "ncbi"
    assert metadata["database_name"] == "refseq_genomic"


def test_fasta_setup_builds_missing_database(
    tmp_path,
    monkeypatch,
):
    """Test custom FASTA source builds a database."""
    reference_fasta = (
        tmp_path
        / "references.fasta"
    )
    write_file(
        reference_fasta,
        ">reference\nATGC\n",
    )

    validation_results = iter([
        False,
        True,
    ])

    monkeypatch.setattr(
        setup_blast_database,
        "validate_database",
        lambda prefix, logger: next(
            validation_results
        ),
    )
    monkeypatch.setattr(
        setup_blast_database,
        "build_fasta_database",
        lambda **kwargs: 0,
    )

    metadata_file = tmp_path / "metadata.json"
    done_file = tmp_path / "blast.done"

    result = setup_blast_database.setup_fasta_database(
        reference_fasta=reference_fasta,
        database_prefix=(
            tmp_path
            / "blast"
            / "fish_mitogenomes"
        ),
        database_title="Fish mitochondrial genomes",
        parse_seqids=True,
        overwrite=False,
        metadata_file=metadata_file,
        done_file=done_file,
        logger=DummyLogger(),
    )

    assert result == 0
    assert metadata_file.exists()
    assert done_file.exists()