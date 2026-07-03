"""fastqc_stats.py

Parser for extracting FastQC statistics from FastQC outputs.
"""

# Imports
from dataclasses import dataclass, asdict

@dataclass(frozen = True)
class FastQCStats:
    """Data model for FastQC statistics.
    
    Attributes:
        sample_id: str
        total_sequences: int
        sequence_length: int
        gc_content_percent: float
        per_base_quality: dict[str, float]
    """
    sample_id: str
    qc_stage: str
    source_file: str
    overall_status: str
    module_statuses: dict[str, str]

    def to_dict(self) -> dict:
        """Convert the FastQCStats object to a dictionary.

        Returns:
            A dictionary representation of the FastQCStats object.
        """
        # Using asdict to convert the dataclass to a dictionary.
        data = asdict(self)

        # Adding module_statuses to dictionary.
        data["module_statuses"] = "; ".join(
            f"{module}={status}"
            for module, status in self.module_statuses.items()
        )

        # Returning dictionary.
        return data