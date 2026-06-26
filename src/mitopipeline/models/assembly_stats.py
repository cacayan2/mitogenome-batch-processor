"""assembly_stats.py

Data model for assembly statistics.
"""

# Imports
from dataclasses import dataclass
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