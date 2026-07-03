"""annotation_stats.py

Data model for annotation statistics. 
"""

# Imports
from dataclasses import dataclass, asdict

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

    def to_dict(self) -> dict:
        """Convert the AnnotationStats object to a dictionary.

        Returns:
            A dictionary representation of the AnnotationStats object.
        """
        # Using asdict to convert the dataclass to a dictionary.
        data = asdict(self)

        # Adding warnings to dictionary.
        if self.warnings is not None:
            data["warnings"] = "; ".join(self.warnings)

        # Returning dictionary.
        return data