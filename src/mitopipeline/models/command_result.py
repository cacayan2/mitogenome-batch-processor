"""command_result.py

This module contains the CommandResult class, specifying the behavior associated with running a command.
"""

from datetime import datetime

class CommandResult:
    """
    CommandResult class - specifies the behavior associated with running a command.
    """
    def __init__(self, command: str, 
                 return_code: int, 
                 stdout: str, 
                 stderr: str, 
                 runtime_seconds: float, 
                 success: bool, 
                 tool_name: str | None = None,
                 started_at: datetime | None = None,
                 ended_at: datetime | None = None,
                 ):
        """Initializes a CommandResult object.
        
        Args:
            command (str): The command that was run.
            return_code (int): The return code of the command.
            stdout (str): The standard output of the command.
            stderr (str): The standard error of the command.
            runtime_seconds (float): The runtime of the command in seconds.
            success (bool): Whether the command was successful or not.
            tool_name (str, optional): The tool name. Defaults to None.
            sample_id (str, optional): The sample ID. Defaults to None.
            started_at (datetime, optional): The start time of the command. Defaults to None.
            ended_at (datetime, optional): The end time of the command. Defaults to None.
        """
        self.tool_name = tool_name
        self.started_at = started_at
        self.ended_at = ended_at
        self.command = command
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.runtime_seconds = runtime_seconds
        self.success = success
        self.tool_name = tool_name
        self.started_at = started_at
        self.ended_at = ended_at