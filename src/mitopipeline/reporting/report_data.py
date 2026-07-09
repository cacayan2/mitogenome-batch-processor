"""report_data.py

Aggregate existing pipeline statistics into report-ready data.
"""

# Imports
import csv
import logging
from pathlib import Path

from mitopipeline.models.report_data import (
    SampleReportData,
)
from mitopipeline.stats.annotation_stats import (
    parse_annotation_stats,
)
from mitopipeline.stats.visualization_stats import (
    build_circular_map_data,
)
from mitopipeline.stats.assembly_stats import (
    parse_assembly_stats,
)
from mitopipeline.stats.blast_stats import (
    parse_top_blast_matches,
)
from mitopipeline.stats.fastp_stats import (
    parse_fastp_json,
)
from mitopipeline.stats.phylogeny_stats import (
    parse_iqtree_model,
    validate_newick_tree,
)



def read_sample_metadata(
        runtime_manifest_path: str | Path,
        sample_id: str,
        logger: logging.Logger | None = None,
) -> dict[str, str]:
    """Read one sample from the normalized runtime manifest.

    Args:
        runtime_manifest_path (str | Path): Runtime manifest TSV.
        sample_id (str): Sample identifier.
        logger (logging.Logger | None, optional): Logger to use.

    Returns:
        dict[str, str]: Runtime-manifest row.

    Raises:
        FileNotFoundError: If the manifest does not exist.
        ValueError: If the sample is not present.
    """
    runtime_manifest_path = Path(
        runtime_manifest_path
    )

    if not runtime_manifest_path.exists():
        raise FileNotFoundError(
            f"Runtime manifest not found: "
            f"{runtime_manifest_path}."
        )

    with runtime_manifest_path.open(
            "r",
            encoding="utf-8",
            newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        for row in reader:
            if row.get(
                "sample_id",
                "",
            ).strip() != sample_id:
                continue

            metadata = {
                key: value.strip()
                for key, value in row.items()
                if key is not None
                and value is not None
                and value.strip()
            }

            if logger is not None:
                logger.info(
                    f"Loaded runtime metadata for "
                    f"sample {sample_id}."
                )

            return metadata

    raise ValueError(
        f"Sample {sample_id} was not found in "
        f"{runtime_manifest_path}."
    )


def build_output_paths(
        job_directory: str | Path,
        sample_id: str,
) -> dict[str, Path]:
    """Construct known pipeline output paths for one sample.

    Args:
        job_directory (str | Path): Pipeline job directory.
        sample_id (str): Sample identifier.

    Returns:
        dict[str, Path]: Named pipeline paths.
    """
    job_directory = Path(
        job_directory
    )

    return {
        "runtime_manifest": (
            job_directory
            / "metadata"
            / "runtime_manifest.tsv"
        ),
        "fastp_json": (
            job_directory
            / "trimming"
            / f"{sample_id}.fastp.json"
        ),
        "fastp_html": (
            job_directory
            / "trimming"
            / f"{sample_id}.fastp.html"
        ),
        "assembly_fasta": (
            job_directory
            / "assembly"
            / f"{sample_id}.fasta"
        ),
        "annotation_directory": (
            job_directory
            / "annotation"
            / sample_id
        ),
        "visualization_png": (
            job_directory
            / "visualization"
            / f"{sample_id}.circular_mitogenome.png"
        ),
        "visualization_svg": (
            job_directory
            / "visualization"
            / f"{sample_id}.circular_mitogenome.svg"
        ),
        "visualization_pdf": (
            job_directory
            / "visualization"
            / f"{sample_id}.circular_mitogenome.pdf"
        ),
        "visualization_done": (
            job_directory
            / "visualization"
            / f"{sample_id}.visualization.done"
        ),
        "blast_top_hits": (
            job_directory
            / "phylogeny"
            / "blast"
            / f"{sample_id}.top_hits.tsv"
        ),
        "phylogeny_dataset": (
            job_directory
            / "phylogeny"
            / "datasets"
            / f"{sample_id}.phylogeny.fasta"
        ),
        "alignment_fasta": (
            job_directory
            / "phylogeny"
            / "alignment"
            / f"{sample_id}.aligned.fasta"
        ),
        "iqtree_report": (
            job_directory
            / "phylogeny"
            / "iqtree"
            / f"{sample_id}.maximum_likelihood.iqtree"
        ),
        "newick_tree": (
            job_directory
            / "phylogeny"
            / "trees"
            / f"{sample_id}.maximum_likelihood.nwk"
        ),
        "tree_svg": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.svg"
        ),
        "tree_pdf": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.pdf"
        ),
        "tree_png": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.maximum_likelihood.png"
        ),
        "phylogeny_summary": (
            job_directory
            / "phylogeny"
            / "figures"
            / f"{sample_id}.phylogeny.md"
        ),
    }


def collect_sample_report_data(
        sample_id: str,
        job_directory: str | Path,
        logger: logging.Logger | None = None,
) -> SampleReportData:
    """Aggregate existing pipeline outputs for one report.

    Optional outputs are represented by None when their corresponding
    pipeline stages were not run.

    Args:
        sample_id (str): Sample identifier.
        job_directory (str | Path): Pipeline job directory.
        logger (logging.Logger | None, optional): Logger to use.

    Returns:
        SampleReportData: Aggregated report data.
    """
    job_directory = Path(
        job_directory
    ).resolve()

    paths = build_output_paths(
        job_directory=job_directory,
        sample_id=sample_id,
    )

    metadata = read_sample_metadata(
        runtime_manifest_path=paths[
            "runtime_manifest"
        ],
        sample_id=sample_id,
        logger=logger,
    )

    fastp_stats = None

    if paths[
        "fastp_json"
    ].exists():
        fastp_model = parse_fastp_json(
            json_path=paths[
                "fastp_json"
            ],
            sample_id=sample_id,
            logger=logger,
        )

        fastp_stats = fastp_model.to_dict()

    assembly_stats = None

    if paths[
        "assembly_fasta"
    ].exists():
        assembly_model = parse_assembly_stats(
            sample_id=sample_id,
            fasta_path=paths[
                "assembly_fasta"
            ],
            logger=logger,
        )

        assembly_stats = assembly_model.to_dict()

    annotation_stats = None

    if paths[
        "annotation_directory"
    ].exists():
        try:
            annotation_model = parse_annotation_stats(
                sample_id=sample_id,
                annotation_directory=paths[
                    "annotation_directory"
                ],
                logger=logger,
            )

            annotation_stats = (
                annotation_model.to_dict()
            )

        except FileNotFoundError:
            if logger is not None:
                logger.warning(
                    "Annotation directory exists, but no "
                    f"GFF was found for {sample_id}."
                )

    visualization_stats = None

    annotation_gff = (
        paths["annotation_directory"]
        / "result.gff"
    )

    annotation_fasta = (
        paths["annotation_directory"]
        / "result.fas"
    )

    if (
        annotation_gff.exists()
        and annotation_fasta.exists()
        and paths["visualization_done"].exists()
    ):
        map_data = build_circular_map_data(
            sample_id=sample_id,
            gff_path=annotation_gff,
            fasta_path=annotation_fasta,
            logger=logger,
        )

    visualization_stats = map_data.to_dict()

    blast_matches = None

    if paths[
        "blast_top_hits"
    ].exists():
        blast_matches = parse_top_blast_matches(
            top_hits_path=paths[
                "blast_top_hits"
            ],
            logger=logger,
        )

    phylogeny_model = parse_iqtree_model(
        paths[
            "iqtree_report"
        ]
    )

    phylogeny_tip_count = None

    if paths[
        "newick_tree"
    ].exists():
        tree = validate_newick_tree(
            tree_path=paths[
                "newick_tree"
            ],
            expected_tip_count=7,
            logger=logger,
        )

        phylogeny_tip_count = len(
            tree.get_terminals()
        )

    if logger is not None:
        logger.info(
            f"Collected report data for sample "
            f"{sample_id}."
        )

    return SampleReportData(
        sample_id=sample_id,
        metadata=metadata,
        fastp_stats=fastp_stats,
        assembly_stats=assembly_stats,
        annotation_stats=annotation_stats,
        visualization_stats=visualization_stats,
        blast_matches=blast_matches,
        phylogeny_model=phylogeny_model,
        phylogeny_tip_count=phylogeny_tip_count,
        output_paths=paths,
    )