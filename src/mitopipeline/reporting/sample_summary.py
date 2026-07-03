"""sample_summary.py

Build per-sample summary objects from statistics. 
"""

# Imports
from mitopipeline.models.sample_summary import SampleSummary
from mitopipeline.models.assembly_stats import AssemblyStats
from mitopipeline.models.annotation_stats import AnnotationStats

def calculate_reads_retained_percent(
        raw_read_count: int | None,
        trimmed_read_count: int | None
) -> float | None:
    """Calculate the percentage of reads retained after trimming.

    Args:
        raw_read_count: The number of raw reads.
        trimmed_read_count: The number of reads after trimming.

    Returns:
        The percentage of reads retained, or None if either count is None.
    """

    # If either count is None, return None.
    if raw_read_count is None or trimmed_read_count is None: return None

    # If raw_read_count is 0, return None to avoid division by zero.
    if raw_read_count == 0: return None

    # Calculate the percentage of reads retained.
    return round((trimmed_read_count / raw_read_count) * 100, 2)

def build_sample_summary(
        sample_id: str,
        assembly_stats: AssemblyStats | None = None,
        annotation_stats: AnnotationStats | None = None,
        raw_read_count: int | None = None,
        trimmed_read_count: int | None = None,
) -> SampleSummary:
    """Build a SampleSummary object from assembly and annotation statistics.

    Args:
        sample_id: The sample ID.
        assembly_stats: The assembly statistics.
        annotation_stats: The annotation statistics.
        raw_read_count: The number of raw reads.
        trimmed_read_count: The number of reads after trimming.

    Returns:
        A SampleSummary object.
    """
    return SampleSummary(
        sample_id = sample_id,
        raw_read_count = raw_read_count,
        trimmed_read_count = trimmed_read_count,
        reads_retained_percent = calculate_reads_retained_percent(raw_read_count, trimmed_read_count),
        fasta_path = assembly_stats.fasta_path if assembly_stats else None,
        contig_count = assembly_stats.contig_count if assembly_stats else None,
        total_length_bp = assembly_stats.total_length_bp if assembly_stats else None,
        gc_content_percent = assembly_stats.gc_content_percent if assembly_stats else None,
        circularization_status = assembly_stats.circularization_status if assembly_stats else None,
        assembly_runtime_seconds = assembly_stats.runtime_seconds if assembly_stats else None,
        cds_count = annotation_stats.cds_count if annotation_stats else None,
        trna_count = annotation_stats.trna_count if annotation_stats else None,
        rrna_count = annotation_stats.rrna_count if annotation_stats else None,
        gene_count = annotation_stats.gene_count if annotation_stats else None,
        annotation_feature_count = annotation_stats.feature_count if annotation_stats else None,
        annotation_warnings = annotation_stats.warnings if annotation_stats else None
    )
