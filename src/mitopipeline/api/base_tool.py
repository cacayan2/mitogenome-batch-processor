"""base_tool.py

This module contains base functionality for tool classes - this is abstract.
"""

# Imports
from abc import ABC, abstractmethod
from mitopipeline.models.command_result import CommandResult
from logging import Logger
from pathlib import Path
import time
from datetime import datetime
import subprocess

class BaseTool(ABC):
    def __init__(self, tool_name: str, 
                 working_dir: Path, 
                 logger: Logger | None = None) -> None:
        """
        Initializes a BaseTool object.

        Args:
            tool_name (str): The name of the tool.
            working_dir (Path): The working directory for the tool.
            logger (Logger | None, optional): The logger to use. Defaults to None.

        Returns:
            None
        """
        self.tool_name = tool_name
        self.working_dir = working_dir
        self.logger = logger
        
    @abstractmethod
    def validate_inputs(self):
        """Validates the inputs for the tool. Must be implemented in objects that inherit this class."""
        pass

    @abstractmethod
    def build_command(self) -> list[str]:
        """Builds the command for the tool. Must be implemented in objects that inherit this class."""
        pass

    @abstractmethod
    def validate_outputs(self):
        """Validates the outputs for the tool. Must be implemented in objects that inherit this class."""
        pass

    def run(self) -> CommandResult:
        """Runs the tool and returns a CommandResult object.
        
        Returns:
            CommandResult: The result of running the tool.
        """

        # Validate inputs.
        self.validate_inputs()

        # Construct command.
        command = self.build_command()

        # Time metadata.
        start_time = time.perf_counter()
        started_at = datetime.now()

        if self.logger is not None:
            self.logger.info(f"({self.tool_name}) Starting execution.")
            self.logger.debug(f"({self.tool_name}) Command: {command}")
            self.logger.debug(f"({self.tool_name}) Working directory: {self.working_dir}")

        # Run command.
        completed = subprocess.run(
            command,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
        )

        end_time = time.perf_counter()
        ended_at = datetime.now()

        # Build CommandResult.
        command_result = CommandResult(
            command=command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            runtime_seconds=end_time - start_time,
            success=completed.returncode == 0,
            tool_name=self.tool_name,
            started_at=started_at,
            ended_at=ended_at,
        )

        if self.logger is not None:
            self.logger.info(f"({self.tool_name}) Execution finished with return code {command_result.return_code}.")
            self.logger.debug(f"({self.tool_name}) Runtime seconds: {command_result.runtime_seconds}")
            self.logger.debug(f"({self.tool_name}) stdout: {command_result.stdout}")
            self.logger.debug(f"({self.tool_name}) stderr: {command_result.stderr}")

        # If external tool failed, return result without validating outputs.
        if not command_result.success:
            if self.logger is not None:
                self.logger.error(f"({self.tool_name}) Execution failed with return code {command_result.return_code}.")
            return command_result

        # Only validate outputs after successful execution.
        self.validate_outputs()

        return command_result