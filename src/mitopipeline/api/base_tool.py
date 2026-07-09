"""Shared execution behavior for external command-line tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger
from pathlib import Path
import shlex
import subprocess
import time

from mitopipeline.models.command_result import CommandResult


class BaseTool(ABC):
    """Base class for external command-line tool wrappers."""

    def __init__(
        self,
        tool_name: str,
        working_dir: Path,
        logger: Logger | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.working_dir = Path(working_dir)
        self.logger = logger

    @abstractmethod
    def validate_inputs(self) -> None:
        """Validate command inputs."""

    @abstractmethod
    def build_command(self) -> list[str]:
        """Build the external command."""

    @abstractmethod
    def validate_outputs(self) -> None:
        """Validate required command outputs."""

    def run(self) -> CommandResult:
        """Execute the tool and return structured execution metadata."""
        context = self._log_context()

        if self.logger is not None:
            self.logger.info(
                "%s Validating inputs.",
                context,
            )

        self.validate_inputs()
        command = self.build_command()

        start_time = time.perf_counter()
        started_at = datetime.now()

        if self.logger is not None:
            self.logger.info(
                "%s Starting execution.",
                context,
            )
            self.logger.debug(
                "%s Command: %s",
                context,
                shlex.join(command),
            )
            self.logger.debug(
                "%s Working directory: %s",
                context,
                self.working_dir,
            )

        completed = subprocess.run(
            command,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
        )

        runtime_seconds = time.perf_counter() - start_time
        ended_at = datetime.now()

        command_result = CommandResult(
            command=command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            runtime_seconds=runtime_seconds,
            success=completed.returncode == 0,
            tool_name=self.tool_name,
            started_at=started_at,
            ended_at=ended_at,
        )

        if self.logger is not None:
            self.logger.info(
                "%s Execution finished with return code %d "
                "after %.2f seconds.",
                context,
                command_result.return_code,
                command_result.runtime_seconds,
            )
            self.logger.debug(
                "%s stdout:\n%s",
                context,
                command_result.stdout,
            )
            self.logger.debug(
                "%s stderr:\n%s",
                context,
                command_result.stderr,
            )

        if not command_result.success:
            if self.logger is not None:
                self.logger.error(
                    "%s External command failed.",
                    context,
                )
            return command_result

        if self.logger is not None:
            self.logger.info(
                "%s Normalizing and validating outputs.",
                context,
            )

        self.postprocess_outputs()
        self.validate_outputs()

        if self.logger is not None:
            self.logger.info(
                "%s Completed successfully.",
                context,
            )

        return command_result

    def postprocess_outputs(self) -> None:
        """Optionally normalize outputs after successful execution."""

    def _log_context(self) -> str:
        """Return a tool-and-sample label for console messages."""
        sample_id = getattr(self, "sample_id", None)

        if sample_id is None:
            sample = getattr(self, "sample", None)
            sample_id = getattr(sample, "sample_id", None)

        if sample_id:
            return f"[{sample_id}] ({self.tool_name})"

        return f"({self.tool_name})"
