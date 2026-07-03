"""annotation_stats.py

Data model for annotation statistics. 
"""

# Imports
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class AnnotationStats:
    """Data model for assembly statistics.
    
    Attributes:
        sample_id: str
        cds_count: int
        trna_count: int
        rrna_count: int
        gene_count: int
        feature_count: int
        warnings: list
    """
    sample_id: str
    cds_count: int
    trna_count: int
    rrna_count: int
    gene_count: int
    feature_count: int
    warnings: list | None = None