"""test_mitos2_api.py

Unit tests for the MITOS2 API wrapper.
"""

# Imports
from pathlib import Path
import pytest

from mitopipeline.api.mitos2 import MITOS2Runner


def write_file(path: Path, contents: str = "test\n") -> None:
    """Write text to a file, creating parent directories as needed.

    Args:
        path (Path): File path.
        contents (str, optional): File contents. Defaults to "test\n".
    """

    # Creating parent directory.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Writing file contents.
    path.write_text(contents, encoding="utf-8")


def make_reference_dir(tmp_path: Path) -> Path:
    """Create a minimal MITOS2 reference directory structure.

    Args:
        tmp_path (Path): Temporary pytest directory.

    Returns:
        Path: MITOS2 reference root.
    """

    # Creating reference root and version directory.
    refdir = tmp_path / "resources" / "mitos"
    refseq = refdir / "refseq89m"
    refseq.mkdir(parents=True, exist_ok=True)

    # Creating minimal expected reference contents.
    write_file(refseq / "auxinfo.json", "{}\n")

    # Returning reference root.
    return refdir


def make_runner(tmp_path: Path) -> MITOS2Runner:
    """Create a valid MITOS2Runner for tests.

    Args:
        tmp_path (Path): Temporary pytest directory.

    Returns:
        MITOS2Runner: Configured MITOS2Runner.
    """

    # Defining paths.
    input_fasta = tmp_path / "assembly" / "sample_001.fasta"
    output_dir = tmp_path / "annotation" / "sample_001"
    refdir = make_reference_dir(tmp_path)

    # Creating input FASTA.
    write_file(input_fasta, ">sample_001\nATGCATGCATGC\n")

    # Returning runner.
    return MITOS2Runner(
        input_fasta=input_fasta,
        output_dir=output_dir,
        working_dir=tmp_path,
        genetic_code=2,
        refseqver="refseq89m",
        refdir=refdir,
        circular=True,
        noplots=False,
        zip_output=False,
        best=False,
        ncbicode=False,
    )


def make_valid_outputs(output_dir: Path) -> None:
    """Create deterministic MITOS2-like output files.

    Args:
        output_dir (Path): MITOS2 output directory.
    """

    # Creating output directories.
    (output_dir / "blast" / "prot").mkdir(parents=True, exist_ok=True)
    (output_dir / "blast" / "nuc").mkdir(parents=True, exist_ok=True)
    (output_dir / "mitfi-global").mkdir(parents=True, exist_ok=True)

    # Creating required final outputs.
    write_file(output_dir / "result.bed", "sequence\t0\t100\tcox1\n")
    write_file(output_dir / "result.faa", ">cox1\nMTESTSEQ\n")
    write_file(output_dir / "result.fas", ">cox1\nATGCATGC\n")
    write_file(output_dir / "result.geneorder", "cox1 trnA rrnS\n")
    write_file(
        output_dir / "result.gff",
        "sequence\tMITOS2\tgene\t1\t100\t.\t+\t.\tID=cox1;Name=cox1\n",
    )
    write_file(output_dir / "result.mitos", "MITOS2 result\n")
    write_file(output_dir / "result.seq", ">sequence\nATGCATGCATGC\n")
    write_file(output_dir / "stst.dat", "status\n")

    # Creating representative intermediate files.
    write_file(output_dir / "blast" / "prot" / "sequence.fas-0.cox1.blast", "blast\n")
    write_file(output_dir / "blast" / "nuc" / "sequence.fas-0.OH.blast", "blast\n")
    write_file(output_dir / "mitfi-global" / "sequence.fas-0_tRNAout.nc", "mitfi\n")


def test_mitos2_runner_validate_inputs_accepts_valid_inputs(tmp_path):
    """Test validate_inputs accepts valid MITOS2 inputs."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Validating inputs.
    runner.validate_inputs()


def test_mitos2_runner_validate_inputs_raises_for_missing_fasta(tmp_path):
    """Test validate_inputs raises if input FASTA is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Removing input FASTA.
    runner.input_fasta.unlink()

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_mitos2_runner_validate_inputs_raises_for_empty_fasta(tmp_path):
    """Test validate_inputs raises if input FASTA is empty."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Emptying input FASTA.
    runner.input_fasta.write_text("", encoding="utf-8")

    # Checking error.
    with pytest.raises(ValueError):
        runner.validate_inputs()


def test_mitos2_runner_validate_inputs_raises_for_missing_refdir(tmp_path):
    """Test validate_inputs raises if reference root is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Removing reference root.
    runner.refdir = tmp_path / "missing_refdir"

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_mitos2_runner_validate_inputs_raises_for_missing_refseqver(tmp_path):
    """Test validate_inputs raises if reference version directory is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Changing reference version.
    runner.refseqver = "missing_refseq"

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_inputs()


def test_mitos2_runner_build_command_circular_default(tmp_path):
    """Test build_command creates a circular MITOS2 command by default."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Building command.
    command = runner.build_command()

    # Checking command.
    assert command[:4] == [
        "conda",
        "run",
        "-n",
        "mito-annotation",
    ]
    assert command[4] == "runmitos.py"
    assert "-i" in command
    assert str(runner.input_fasta) in command
    assert "--code" in command
    assert "2" in command
    assert "--outdir" in command
    assert str(runner.output_dir) in command
    assert "--refdir" in command
    assert str(runner.refdir) in command
    assert "--refseqver" in command
    assert "refseq89m" in command

    # Circular mode should not pass --linear.
    assert "--linear" not in command


def test_mitos2_runner_build_command_linear_when_requested(tmp_path):
    """Test build_command adds --linear when circular is False."""

    # Creating runner.
    runner = make_runner(tmp_path)
    runner.circular = False

    # Building command.
    command = runner.build_command()

    # Checking command.
    assert "--linear" in command


def test_mitos2_runner_build_command_adds_optional_flags(tmp_path):
    """Test build_command adds selected optional MITOS2 flags."""

    # Creating runner.
    runner = make_runner(tmp_path)
    runner.noplots = True
    runner.zip_output = True
    runner.best = True
    runner.ncbicode = True

    # Building command.
    command = runner.build_command()

    # Checking optional flags.
    assert "--noplots" in command
    assert "--zip" in command
    assert "--best" in command
    assert "--ncbicode" in command


def test_mitos2_runner_build_command_creates_output_dir(tmp_path):
    """Test build_command creates MITOS2 output directory."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Checking output directory does not exist yet.
    assert not runner.output_dir.exists()

    # Building command.
    runner.build_command()

    # Checking output directory exists.
    assert runner.output_dir.exists()


def test_mitos2_runner_validate_outputs_accepts_valid_outputs(tmp_path):
    """Test validate_outputs accepts deterministic MITOS2 outputs."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Validating outputs.
    runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_missing_output_dir(tmp_path):
    """Test validate_outputs raises if output directory is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_missing_required_file(tmp_path):
    """Test validate_outputs raises if a required MITOS2 output file is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Removing required output.
    (runner.output_dir / "result.gff").unlink()

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_empty_required_file(tmp_path):
    """Test validate_outputs raises if a required MITOS2 output file is empty."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Emptying required output.
    (runner.output_dir / "result.gff").write_text("", encoding="utf-8")

    # Checking error.
    with pytest.raises(ValueError):
        runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_missing_required_directory(tmp_path):
    """Test validate_outputs raises if a required MITOS2 output directory is missing."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Removing required directory.
    for path in (runner.output_dir / "mitfi-global").iterdir():
        path.unlink()
    (runner.output_dir / "mitfi-global").rmdir()

    # Checking error.
    with pytest.raises(FileNotFoundError):
        runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_gff_without_features(tmp_path):
    """Test validate_outputs raises if result.gff has no feature rows."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Replacing GFF with comments only.
    (runner.output_dir / "result.gff").write_text(
        "##gff-version 3\n# comment only\n",
        encoding="utf-8",
    )

    # Checking error.
    with pytest.raises(ValueError):
        runner.validate_outputs()


def test_mitos2_runner_validate_outputs_raises_for_fasta_without_records(tmp_path):
    """Test validate_outputs raises if FASTA-like outputs lack sequence records."""

    # Creating runner.
    runner = make_runner(tmp_path)

    # Creating valid outputs.
    make_valid_outputs(runner.output_dir)

    # Replacing result.faa with invalid FASTA content.
    (runner.output_dir / "result.faa").write_text(
        "not a fasta file\n",
        encoding="utf-8",
    )

    # Checking error.
    with pytest.raises(ValueError):
        runner.validate_outputs()