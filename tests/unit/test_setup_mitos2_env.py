"""test_setup_mitos2_env.py

Unit tests for MITOS2 setup utility.
"""

# Imports
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

from mitopipeline.utils import setup_mitos2_env


def completed_process(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Create a fake subprocess.CompletedProcess."""
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_conda_exists_true(monkeypatch):
    """Test conda_exists returns True when conda is available."""
    # Mocking shutil.which.
    monkeypatch.setattr(setup_mitos2_env.shutil, "which", lambda command: "/usr/bin/conda")

    # Checking result.
    assert setup_mitos2_env.conda_exists() is True


def test_conda_exists_false(monkeypatch):
    """Test conda_exists returns False when conda is unavailable."""
    # Mocking shutil.which.
    monkeypatch.setattr(setup_mitos2_env.shutil, "which", lambda command: None)

    # Checking result.
    assert setup_mitos2_env.conda_exists() is False


def test_conda_env_exists_true(monkeypatch):
    """Test conda_env_exists returns True when environment is listed."""
    # Creating logger.
    logger = Mock()

    # Mocking run_command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(
            returncode=0,
            stdout="base /path/base\nmito-annotation /path/mito-annotation\n",
        ),
    )

    # Checking result.
    assert setup_mitos2_env.conda_env_exists("mito-annotation", logger) is True


def test_conda_env_exists_false(monkeypatch):
    """Test conda_env_exists returns False when environment is not listed."""
    # Creating logger.
    logger = Mock()

    # Mocking run_command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(
            returncode=0,
            stdout="base /path/base\nother-env /path/other-env\n",
        ),
    )

    # Checking result.
    assert setup_mitos2_env.conda_env_exists("mito-annotation", logger) is False


def test_conda_env_exists_false_when_conda_command_fails(monkeypatch):
    """Test conda_env_exists returns False when conda env list fails."""
    # Creating logger.
    logger = Mock()

    # Mocking run_command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(returncode=1, stderr="error"),
    )

    # Checking result.
    assert setup_mitos2_env.conda_env_exists("mito-annotation", logger) is False


def test_create_conda_env_raises_for_missing_env_file(tmp_path):
    """Test create_conda_env raises if env file is missing."""
    # Creating logger.
    logger = Mock()

    # Defining missing env file.
    env_file = tmp_path / "missing.yaml"

    # Checking error.
    with pytest.raises(FileNotFoundError):
        setup_mitos2_env.create_conda_env("mito-annotation", env_file, logger)


def test_create_conda_env_runs_expected_command(tmp_path, monkeypatch):
    """Test create_conda_env runs conda env create."""
    # Creating logger.
    logger = Mock()

    # Creating env file.
    env_file = tmp_path / "annotation.yaml"
    env_file.write_text("name: mito-annotation\n", encoding="utf-8")

    # Capturing command.
    commands = []

    def fake_run_command(command, logger):
        commands.append(command)
        return completed_process(returncode=0)

    # Mocking run_command.
    monkeypatch.setattr(setup_mitos2_env, "run_command", fake_run_command)

    # Running function.
    setup_mitos2_env.create_conda_env("mito-annotation", env_file, logger)

    # Checking command.
    assert commands == [["conda", "env", "create", "-f", str(env_file)]]


def test_create_conda_env_raises_when_command_fails(tmp_path, monkeypatch):
    """Test create_conda_env raises when conda env create fails."""
    # Creating logger.
    logger = Mock()

    # Creating env file.
    env_file = tmp_path / "annotation.yaml"
    env_file.write_text("name: mito-annotation\n", encoding="utf-8")

    # Mocking failed command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(returncode=1, stderr="failed"),
    )

    # Checking error.
    with pytest.raises(RuntimeError):
        setup_mitos2_env.create_conda_env("mito-annotation", env_file, logger)


def test_verify_mitos2_runs_help_command(monkeypatch):
    """Test verify_mitos2 runs conda run help command."""
    # Creating logger.
    logger = Mock()

    # Capturing command.
    commands = []

    def fake_run_command(command, logger):
        commands.append(command)
        return completed_process(returncode=0)

    # Mocking run_command.
    monkeypatch.setattr(setup_mitos2_env, "run_command", fake_run_command)

    # Running function.
    setup_mitos2_env.verify_mitos2("mito-annotation", logger)

    # Checking command.
    assert commands == [
        ["conda", "run", "-n", "mito-annotation", "runmitos.py", "--help"]
    ]


def test_verify_mitos2_raises_when_help_fails(monkeypatch):
    """Test verify_mitos2 raises when MITOS2 help command fails."""
    # Creating logger.
    logger = Mock()

    # Mocking failed command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(returncode=1, stderr="failed"),
    )

    # Checking error.
    with pytest.raises(RuntimeError):
        setup_mitos2_env.verify_mitos2("mito-annotation", logger)


def test_setup_reference_data_runs_expected_command(tmp_path, monkeypatch):
    """Test setup_reference_data delegates to reference setup utility."""
    # Creating logger.
    logger = Mock()

    # Capturing command.
    commands = []

    def fake_run_command(command, logger):
        commands.append(command)
        return completed_process(returncode=0)

    # Mocking run_command.
    monkeypatch.setattr(setup_mitos2_env, "run_command", fake_run_command)

    # Running function.
    setup_mitos2_env.setup_reference_data(
        refseqver="refseq89m",
        refdir=tmp_path / "resources" / "mitos",
        zenodo_record="4284483",
        done_file=tmp_path / "done.txt",
        log_file=tmp_path / "setup.log",
        overwrite_reference=False,
        logger=logger,
    )

    # Checking command.
    assert commands[0][:3] == ["python", "-m", "mitopipeline.utils.setup_mitos2_reference_data"]
    assert "--refseqver" in commands[0]
    assert "refseq89m" in commands[0]
    assert "--overwrite" not in commands[0]


def test_setup_reference_data_adds_overwrite_flag(tmp_path, monkeypatch):
    """Test setup_reference_data adds overwrite flag when requested."""
    # Creating logger.
    logger = Mock()

    # Capturing command.
    commands = []

    def fake_run_command(command, logger):
        commands.append(command)
        return completed_process(returncode=0)

    # Mocking run_command.
    monkeypatch.setattr(setup_mitos2_env, "run_command", fake_run_command)

    # Running function.
    setup_mitos2_env.setup_reference_data(
        refseqver="refseq89m",
        refdir=tmp_path / "resources" / "mitos",
        zenodo_record="4284483",
        done_file=tmp_path / "done.txt",
        log_file=tmp_path / "setup.log",
        overwrite_reference=True,
        logger=logger,
    )

    # Checking overwrite flag.
    assert "--overwrite" in commands[0]


def test_setup_reference_data_raises_when_command_fails(tmp_path, monkeypatch):
    """Test setup_reference_data raises when reference setup fails."""
    # Creating logger.
    logger = Mock()

    # Mocking failed command.
    monkeypatch.setattr(
        setup_mitos2_env,
        "run_command",
        lambda command, logger: completed_process(returncode=1, stderr="failed"),
    )

    # Checking error.
    with pytest.raises(RuntimeError):
        setup_mitos2_env.setup_reference_data(
            refseqver="refseq89m",
            refdir=tmp_path / "resources" / "mitos",
            zenodo_record="4284483",
            done_file=tmp_path / "done.txt",
            log_file=tmp_path / "setup.log",
            overwrite_reference=False,
            logger=logger,
        )