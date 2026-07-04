"""test_setup_blast_database.py

Unit tests for local BLAST database setup.
"""

# Imports
from pathlib import Path
from types import SimpleNamespace

from mitopipeline.utils import setup_blast_database


class DummyLogger:
    """Minimal logger implementation for database setup tests."""

    def info(self, message):
        pass

    def debug(self, message):
        pass

    def error(self, message):
        pass

    def exception(self, message):
        pass


def write_file(path: Path, contents: str = "test\n") -> None:
    """Write a text file and create parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def make_database_files(database_prefix: Path) -> None:
    """Create minimal required nucleotide database files."""
    write_file(Path(f"{database_prefix}.nhr"))
    write_file(Path(f"{database_prefix}.nin"))
    write_file(Path(f"{database_prefix}.nsq"))


def make_args(tmp_path: Path) -> SimpleNamespace:
    """Create database setup arguments."""
    return SimpleNamespace(
        input_fasta=str(tmp_path / "references.fasta"),
        database_prefix=str(
            tmp_path / "blast" / "fish_mito"
        ),
        database_title="Fish mitochondrial genomes",
        done_file=str(
            tmp_path / "setup" / "blast.done"
        ),
        log_file=str(tmp_path / "logs" / "blast.log"),
        metadata_file=str(
            tmp_path / "setup" / "blast.metadata.json"
        ),
        parse_seqids=False,
        overwrite=False,
    )


def test_required_database_files_returns_expected_paths(tmp_path):
    """Test required nucleotide database paths are generated."""
    prefix = tmp_path / "blast" / "fish_mito"

    paths = setup_blast_database.required_database_files(prefix)

    assert paths == [
        Path(f"{prefix}.nhr"),
        Path(f"{prefix}.nin"),
        Path(f"{prefix}.nsq"),
    ]


def test_database_components_exist_returns_true_for_complete_database(
    tmp_path,
):
    """Test complete database components are detected."""
    prefix = tmp_path / "blast" / "fish_mito"
    make_database_files(prefix)

    assert (
        setup_blast_database.database_components_exist(prefix)
        is True
    )


def test_database_components_exist_returns_false_for_partial_database(
    tmp_path,
):
    """Test incomplete database components are detected."""
    prefix = tmp_path / "blast" / "fish_mito"

    write_file(Path(f"{prefix}.nhr"))
    write_file(Path(f"{prefix}.nin"))

    assert (
        setup_blast_database.database_components_exist(prefix)
        is False
    )


def test_database_files_returns_matching_files(tmp_path):
    """Test database_files finds files belonging to a prefix."""
    prefix = tmp_path / "blast" / "fish_mito"

    make_database_files(prefix)
    write_file(Path(f"{prefix}.metadata.json"))
    write_file(prefix.parent / "different_database.nhr")

    files = setup_blast_database.database_files(prefix)

    assert Path(f"{prefix}.nhr") in files
    assert Path(f"{prefix}.nin") in files
    assert Path(f"{prefix}.nsq") in files
    assert Path(f"{prefix}.metadata.json") in files
    assert prefix.parent / "different_database.nhr" not in files


def test_validate_database_returns_false_when_components_missing(
    tmp_path,
):
    """Test validate_database fails before invoking blastdbcmd."""
    prefix = tmp_path / "blast" / "fish_mito"

    result = setup_blast_database.validate_database(
        prefix,
        DummyLogger(),
    )

    assert result is False


def test_validate_database_returns_true_when_blastdbcmd_succeeds(
    tmp_path,
    monkeypatch,
):
    """Test validate_database accepts a readable database."""
    prefix = tmp_path / "blast" / "fish_mito"
    make_database_files(prefix)

    captured = {}

    def fake_run_command(command, logger):
        captured["command"] = command

        return SimpleNamespace(
            returncode=0,
            stdout="Database: fish_mito",
            stderr="",
        )

    monkeypatch.setattr(
        setup_blast_database,
        "run_command",
        fake_run_command,
    )

    result = setup_blast_database.validate_database(
        prefix,
        DummyLogger(),
    )

    assert result is True
    assert captured["command"] == [
        "blastdbcmd",
        "-db",
        str(prefix),
        "-dbtype",
        "nucl",
        "-info",
    ]


def test_validate_database_returns_false_when_blastdbcmd_fails(
    tmp_path,
    monkeypatch,
):
    """Test validate_database rejects an unreadable database."""
    prefix = tmp_path / "blast" / "fish_mito"
    make_database_files(prefix)

    monkeypatch.setattr(
        setup_blast_database,
        "run_command",
        lambda command, logger: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="invalid database",
        ),
    )

    assert (
        setup_blast_database.validate_database(
            prefix,
            DummyLogger(),
        )
        is False
    )


def test_remove_database_files_removes_matching_files(tmp_path):
    """Test removal deletes all files associated with a prefix."""
    prefix = tmp_path / "blast" / "fish_mito"
    make_database_files(prefix)

    setup_blast_database.remove_database_files(
        prefix,
        DummyLogger(),
    )

    assert setup_blast_database.database_files(prefix) == []


def test_build_database_constructs_makeblastdb_command(
    tmp_path,
    monkeypatch,
):
    """Test build_database constructs the expected command."""
    input_fasta = tmp_path / "references.fasta"
    prefix = tmp_path / "temporary" / "fish_mito"
    captured = {}

    write_file(
        input_fasta,
        ">reference\nATGCATGC\n",
    )

    def fake_run_command(command, logger):
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

    return_code = setup_blast_database.build_database(
        input_fasta=input_fasta,
        temporary_prefix=prefix,
        database_title="Fish mitochondrial genomes",
        parse_seqids=True,
        logger=DummyLogger(),
    )

    assert return_code == 0
    assert captured["command"] == [
        "makeblastdb",
        "-in",
        str(input_fasta),
        "-dbtype",
        "nucl",
        "-out",
        str(prefix),
        "-title",
        "Fish mitochondrial genomes",
        "-parse_seqids",
    ]


def test_install_database_moves_database_files(tmp_path):
    """Test temporary database files are moved to final prefix."""
    temporary_prefix = (
        tmp_path
        / "temporary"
        / "fish_mito"
    )
    final_prefix = (
        tmp_path
        / "final"
        / "fish_mito"
    )

    make_database_files(temporary_prefix)

    setup_blast_database.install_database(
        temporary_prefix=temporary_prefix,
        final_prefix=final_prefix,
        logger=DummyLogger(),
    )

    assert Path(f"{final_prefix}.nhr").exists()
    assert Path(f"{final_prefix}.nin").exists()
    assert Path(f"{final_prefix}.nsq").exists()

    assert not Path(f"{temporary_prefix}.nhr").exists()
    assert not Path(f"{temporary_prefix}.nin").exists()
    assert not Path(f"{temporary_prefix}.nsq").exists()


def test_write_done_file_records_database_prefix(tmp_path):
    """Test completion marker contains the database prefix."""
    done_file = tmp_path / "setup" / "blast.done"
    prefix = tmp_path / "blast" / "fish_mito"

    setup_blast_database.write_done_file(
        done_file,
        prefix,
    )

    assert done_file.read_text(
        encoding="utf-8"
    ) == f"{prefix}\n"


def test_main_returns_one_for_missing_reference_fasta(
    tmp_path,
    monkeypatch,
):
    """Test setup fails when reference FASTA is absent."""
    args = make_args(tmp_path)

    monkeypatch.setattr(
        setup_blast_database,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        setup_blast_database,
        "make_logger",
        lambda **kwargs: DummyLogger(),
    )

    assert setup_blast_database.main() == 1


def test_main_skips_valid_existing_database(
    tmp_path,
    monkeypatch,
):
    """Test setup skips rebuilding an existing valid database."""
    args = make_args(tmp_path)

    input_fasta = Path(args.input_fasta)
    database_prefix = Path(args.database_prefix)
    done_file = Path(args.done_file)

    write_file(
        input_fasta,
        ">reference\nATGCATGC\n",
    )
    make_database_files(database_prefix)

    monkeypatch.setattr(
        setup_blast_database,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        setup_blast_database,
        "make_logger",
        lambda **kwargs: DummyLogger(),
    )
    monkeypatch.setattr(
        setup_blast_database,
        "validate_database",
        lambda prefix, logger: True,
    )

    build_called = {"value": False}

    def fake_build_database(**kwargs):
        build_called["value"] = True
        return 0

    monkeypatch.setattr(
        setup_blast_database,
        "build_database",
        fake_build_database,
    )

    result = setup_blast_database.main()

    assert result == 0
    assert build_called["value"] is False
    assert done_file.exists()


def test_main_rejects_partial_database_without_overwrite(
    tmp_path,
    monkeypatch,
):
    """Test partial existing database requires overwrite."""
    args = make_args(tmp_path)

    input_fasta = Path(args.input_fasta)
    database_prefix = Path(args.database_prefix)

    write_file(
        input_fasta,
        ">reference\nATGCATGC\n",
    )
    write_file(Path(f"{database_prefix}.nhr"))

    monkeypatch.setattr(
        setup_blast_database,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        setup_blast_database,
        "make_logger",
        lambda **kwargs: DummyLogger(),
    )

    assert setup_blast_database.main() == 1


def test_main_returns_makeblastdb_failure_code(
    tmp_path,
    monkeypatch,
):
    """Test setup returns makeblastdb's failure code."""
    args = make_args(tmp_path)
    input_fasta = Path(args.input_fasta)

    write_file(
        input_fasta,
        ">reference\nATGCATGC\n",
    )

    monkeypatch.setattr(
        setup_blast_database,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        setup_blast_database,
        "make_logger",
        lambda **kwargs: DummyLogger(),
    )
    monkeypatch.setattr(
        setup_blast_database,
        "build_database",
        lambda **kwargs: 2,
    )

    assert setup_blast_database.main() == 2