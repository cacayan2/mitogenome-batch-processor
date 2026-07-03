"""sample_summary.py

Data model for sample summary statistics. 
"""

# Imports
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen = True)
class SampleSummary:
    """Data model for sample summary statistics.

    Attributes:
        sample_id: str
        raw_read_count: int | None = None
        trimmed_read_count: int | None = None
        reads_retained_percent: float | None = None
        fasta_path: Path | None = None
        contig_count: int | None = None
        total_length_bp: int | None = None
        gc_content_percent: float | None = None
        circularization_status: str | None = None
        assembly_runtime_seconds: float | None = None
        cds_count: int | None = None
        trna_count: int | None = None
        rrna_count: int | None = None
        gene_count: int | None = None
        annotation_feature_count: int | None = None
        annotation_warnings: list[str] | None = None
        best_blast_species: str | None = None
        best_blast_percent_identity: float | None = None
    """
    sample_id: str

    # QC / trimming statistics
    raw_read_count: int | None = None
    trimmed_read_count: int | None = None
    reads_retained_percent: float | None = None

    # Assembly statistics
    fasta_path: Path | None = None
    contig_count: int | None = None
    total_length_bp: int | None = None
    gc_content_percent: float | None = None
    circularization_status: str | None = None
    assembly_runtime_seconds: float | None = None

    # Annotation
    cds_count: int | None = None
    trna_count: int | None = None
    rrna_count: int | None = None
    gene_count: int | None = None
    annotation_feature_count: int | None = None
    annotation_warnings: list[str] | None = None

    # BLAST / Taxonomy
    best_blast_species: str | None = None
    best_blast_percent_identity: float | None = None

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the SampleSummary instance.
        
        Returns
            dict: A dictionary containing the sample summary statistics.
        """
        # Converting dataclass to dictionary.
        data = asdict(self)

        # Converting Path objects to strings.
        if self.fasta_path is not None:
            data["fasta_path"] = str(self.fasta_path)
        
        # Converting list to string.
        if self.annotation_warnings is not None:
            data["annotation_warnings"] = "; ".join(self.annotation_warnings)

        # Returning dictionary.
        return data