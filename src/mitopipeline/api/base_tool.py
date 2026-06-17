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
    def __init__(self, tool_name: str, working_dir: Path, logger: Logger | None = None):
        """
        Initializes a BaseTool object.

        Args:
            tool_name (str): The name of the tool.
            working_dir (Path): The working directory for the tool.
            logger (Logger | None, optional): The logger to use. Defaults to None.
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

        # Constructing the command.
        command = self.build_command()

        # Obtaining time metadata.
        start_time = time.perf_counter()
        started_at = datetime.now()
        # Running the command and logging.
        if self.logger is not None: self.logger.info(f"Running tool: {self.tool_name} at {start_time}, specific command can be found in logfile.")
        if self.logger is not None: self.logger.debug(f"Running command {self.command} in {self.working_dir} at {start_time}.")
        completed = subprocess.run(command, cwd = self.working_dir, capture_output = True, text = True)
        end_time = time.perf_counter()
        ended_at = datetime.now()
        if self.logger is not None: self.logger.info(f"Tool {self.tool_name} completed at {end_time}, specific command can be found in logfile.")
        if self.logger is not None: self.logger.debug(f"Command {self.command} in {self.working_dir} completed at {end_time}.")

        # Constructing the CommandResult object.
        command_result = CommandResult(command, 
                             completed.returncode, 
                             completed.stdout, 
                             completed.stderr, 
                             end_time - start_time,
                             completed.returncode == 0,
                             tool_name = self.tool_name,
                             started_at = started_at,
                             ended_at = ended_at
                             )
        
        # Validating outputs if the command was successful.
        if command_result.success:
            self.validate_outputs()

        # Returning the CommandResult object.
        return command_result
    