"""assembly_stats.py

Data model for assembly statistics.
"""

# Imports
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen = True)
class AssemblyStats:
    """Data model for assembly statistics.
    
    Attributes:
        sample_id: str
        fasta_path: Path
        contig_count: int
        total_length_bp: int
        gc_content_percent: float
        circularization_status: str | None = None
    """
    sample_id: str
    fasta_path: Path
    contig_count: int
    total_length_bp: int
    gc_content_percent: float
    circularization_status: str | None = None
    runtime_seconds: float | None = None

    def to_dict(self) -> dict:
        """Convert the AssemblyStats object to a dictionary.

        Returns:
            A dictionary representation of the AssemblyStats object.
        """
        # Using asdict to convert the dataclass to a dictionary.
        data = asdict(self)

        # Adding fasta_path to dictionary.
        if self.fasta_path is not None:
            data["fasta_path"] = str(self.fasta_path)

        return data