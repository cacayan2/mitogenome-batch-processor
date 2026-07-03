"""fastp_stats.py

Parser for extracting Fastp statistics from Fastp outputs.
"""

# Imports
from dataclasses import dataclass, asdict


@dataclass(frozen = True)
class FastPStats:
    """Data model for Fastp statistics.
    
    Attributes:
        sample_id: str
        reads_in: int
        reads_out: int
        bases_in: int
        bases_out: int
        q20_rate_in: float
        q20_rate_out: float
        q30_rate_in: float
        q30_rate_out: float
        gc_content_in: float
        gc_content_out: float
        reads_removed: int
        bases_removed: int
        read_retention_rate: float
        base_retention_rate: float
        reads_passing_filtering: int
        low_qual_removed: int
        too_many_n_removed: int
        too_short_removed: int
        too_long_removed: int
        adapter_removed_reads: int
        adapter_removed_bases: int
    """
    sample_id: str
    reads_in: int
    reads_out: int
    bases_in: int
    bases_out: int
    q20_rate_in: float
    q20_rate_out: float
    q30_rate_in: float
    q30_rate_out: float
    gc_content_in: float
    gc_content_out: float
    reads_removed: int
    bases_removed: int
    read_retention_rate: float
    base_retention_rate: float
    reads_passing_filtering: int
    low_qual_removed: int
    too_many_n_removed: int
    too_short_removed: int
    too_long_removed: int
    adapter_removed_reads: int
    adapter_removed_bases: int

    def to_dict(self) -> dict:
            """Convert the FastPStats object to a dictionary.

            Returns:
                A dictionary representation of the FastPStats object.
            """
            # Returning dictionary.
            return asdict(self)
