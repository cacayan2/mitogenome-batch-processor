"""test_base_tool.py

Unit tests for BaseTool execution behavior.
"""

# Imports
from pathlib import Path
import shutil
import sys
import pytest

from mitopipeline.api.base_tool import BaseTool
from mitopipeline.models.command_result import CommandResult


class SuccessfulDummyTool(BaseTool):
    """Dummy tool that succeeds."""

    def validate_inputs(self):
        """Validate dummy inputs."""
        return None

    def build_command(self) -> list[str]:
        """Build a successful dummy command."""
        return [
            sys.executable,
            "-c",
            "print('hello from dummy tool')"
        ]

    def validate_outputs(self):
        """Validate dummy outputs."""
        return None


class FailingDummyTool(BaseTool):
    """Dummy tool that fails."""

    def validate_inputs(self):
        """Validate dummy inputs."""
        return None

    def build_command(self) -> list[str]:
        """Build a failing dummy command."""
        return [
            sys.executable,
            "-c",
            "import sys; print('failure message'); sys.exit(1)"
        ]

    def validate_outputs(self):
        """Validate dummy outputs."""
        return None


class OutputCreatingDummyTool(BaseTool):
    """Dummy tool that creates an output file."""

    def __init__(self, tool_name: str, working_dir: Path, output_file: Path, logger=None):
        """Initialize dummy output-creating tool."""
        super().__init__(
            tool_name=tool_name,
            working_dir=working_dir,
            logger=logger
        )
        self.output_file = output_file

    def validate_inputs(self):
        """Validate dummy inputs."""
        return None

    def build_command(self) -> list[str]:
        """Build command that creates an output file."""
        return [
            sys.executable,
            "-c",
            "from pathlib import Path; Path('output.txt').write_text('output created')"
        ]

    def validate_outputs(self):
        """Validate that expected output file exists."""
        if not self.output_file.exists():
            raise FileNotFoundError(f"Expected output file was not created: {self.output_file}")


class MissingOutputDummyTool(BaseTool):
    """Dummy tool that succeeds but does not create expected output."""

    def __init__(self, tool_name: str, working_dir: Path, output_file: Path, logger=None):
        """Initialize dummy missing-output tool."""
        super().__init__(
            tool_name=tool_name,
            working_dir=working_dir,
            logger=logger
        )
        self.output_file = output_file

    def validate_inputs(self):
        """Validate dummy inputs."""
        return None

    def build_command(self) -> list[str]:
        """Build command that succeeds but creates no output."""
        return [
            sys.executable,
            "-c",
            "print('command succeeded but output is missing')"
        ]

    def validate_outputs(self):
        """Validate that expected output file exists."""
        if not self.output_file.exists():
            raise FileNotFoundError(f"Expected output file was not created: {self.output_file}")


def test_base_tool_cannot_be_instantiated_directly():
    """Unit test confirming BaseTool cannot be instantiated directly."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    # Assert statements.
    with pytest.raises(TypeError):
        BaseTool(
            tool_name="base",
            working_dir=test_dir,
            logger=None
        )

    shutil.rmtree(test_dir)


def test_successful_tool_returns_command_result():
    """Unit test for successful BaseTool execution."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    # Creating dummy tool.
    tool = SuccessfulDummyTool(
        tool_name="dummy_success",
        working_dir=test_dir,
        logger=None
    )

    # Running tool.
    result = tool.run()

    # Assert statements.
    assert isinstance(result, CommandResult)
    assert result.success is True
    assert result.return_code == 0
    assert "hello from dummy tool" in result.stdout
    assert result.stderr == ""
    assert result.runtime_seconds >= 0
    assert result.command == [
        sys.executable,
        "-c",
        "print('hello from dummy tool')"
    ]

    shutil.rmtree(test_dir)


def test_failing_tool_returns_failed_command_result():
    """Unit test for failed BaseTool execution."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    # Creating dummy tool.
    tool = FailingDummyTool(
        tool_name="dummy_failure",
        working_dir=test_dir,
        logger=None
    )

    # Running tool.
    result = tool.run()

    # Assert statements.
    assert isinstance(result, CommandResult)
    assert result.success is False
    assert result.return_code != 0
    assert "failure message" in result.stdout
    assert result.runtime_seconds >= 0

    shutil.rmtree(test_dir)


def test_successful_tool_validates_outputs():
    """Unit test for output validation after successful command execution."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")
    output_file = test_dir / "output.txt"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    # Creating dummy tool.
    tool = OutputCreatingDummyTool(
        tool_name="dummy_output",
        working_dir=test_dir,
        output_file=output_file,
        logger=None
    )

    # Running tool.
    result = tool.run()

    # Assert statements.
    assert result.success is True
    assert output_file.exists()
    assert output_file.read_text() == "output created"

    shutil.rmtree(test_dir)


def test_missing_output_raises_error_after_successful_command():
    """Unit test for output validation failure after successful command execution."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")
    output_file = test_dir / "missing_output.txt"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    # Creating dummy tool.
    tool = MissingOutputDummyTool(
        tool_name="dummy_missing_output",
        working_dir=test_dir,
        output_file=output_file,
        logger=None
    )

    # Assert statements.
    with pytest.raises(FileNotFoundError):
        tool.run()

    shutil.rmtree(test_dir)


def test_working_directory_is_used():
    """Unit test confirming command runs in the provided working directory."""

    # Creating temporary test directory.
    test_dir = Path("basetooltest_tmp")
    output_file = test_dir / "cwd_output.txt"

    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir(parents=True)

    class WorkingDirectoryDummyTool(BaseTool):
        """Dummy tool that writes to current working directory."""

        def validate_inputs(self):
            """Validate dummy inputs."""
            return None

        def build_command(self) -> list[str]:
            """Build command that writes output in cwd."""
            return [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('cwd_output.txt').write_text('cwd works')"
            ]

        def validate_outputs(self):
            """Validate output was created in working directory."""
            if not output_file.exists():
                raise FileNotFoundError("Output file was not created in working directory.")

    # Creating dummy tool.
    tool = WorkingDirectoryDummyTool(
        tool_name="dummy_cwd",
        working_dir=test_dir,
        logger=None
    )

    # Running tool.
    result = tool.run()

    # Assert statements.
    assert result.success is True
    assert output_file.exists()
    assert output_file.read_text() == "cwd works"

    shutil.rmtree(test_dir)