"""annotation_stats.py

Extract summary statistics from MITOS2 GFF annotation outputs.
"""

# Imports
import logging
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnnotationStats:
    """Summary statistics for one mitochondrial annotation."""

    sample_id: str
    gff_path: Path
    total_features: int
    feature_counts: dict[str, int]
    feature_names: list[str]

    def to_dict(self) -> dict:
        """Convert annotation statistics into a dictionary."""
        data = asdict(
            self
        )

        data["gff_path"] = str(
            self.gff_path
        )

        return data


def discover_annotation_gff(
        annotation_directory: str | Path,
) -> Path:
    """Locate the primary GFF file under an annotation directory.

    Args:
        annotation_directory (str | Path): MITOS2 output directory.

    Returns:
        Path: Selected GFF file.

    Raises:
        FileNotFoundError: If no GFF file can be found.
    """
    annotation_directory = Path(
        annotation_directory
    )

    if not annotation_directory.exists():
        raise FileNotFoundError(
            f"Annotation directory not found: "
            f"{annotation_directory}."
        )

    if not annotation_directory.is_dir():
        raise ValueError(
            f"Annotation path is not a directory: "
            f"{annotation_directory}."
        )

    candidates = [
        *annotation_directory.rglob(
            "*.gff"
        ),
        *annotation_directory.rglob(
            "*.gff3"
        ),
    ]

    candidates = sorted(
        set(candidates),
        key=lambda path: (
            path.name.lower() not in {
                "result.gff",
                "result.gff3",
            },
            len(path.parts),
            path.name.lower(),
        ),
    )

    if not candidates:
        raise FileNotFoundError(
            "No GFF or GFF3 annotation file was found under "
            f"{annotation_directory}."
        )

    return candidates[0]


def parse_gff_attributes(
        attributes_text: str,
) -> dict[str, str]:
    """Parse GFF3 attributes into a dictionary.

    Args:
        attributes_text (str): GFF attributes column.

    Returns:
        dict[str, str]: Parsed attributes.
    """
    attributes: dict[str, str] = {}

    for entry in attributes_text.split(
            ";"
    ):
        entry = entry.strip()

        if not entry:
            continue

        if "=" not in entry:
            continue

        key, value = entry.split(
            "=",
            maxsplit=1,
        )

        attributes[
            key.strip()
        ] = value.strip()

    return attributes


def parse_annotation_stats(
        sample_id: str,
        annotation_directory: str | Path,
        logger: logging.Logger | None = None,
) -> AnnotationStats:
    """Extract annotation statistics from a MITOS2 GFF file.

    Args:
        sample_id (str): Sample identifier.
        annotation_directory (str | Path): MITOS2 output directory.
        logger (logging.Logger | None, optional): Logger to use.

    Returns:
        AnnotationStats: Parsed annotation statistics.
    """
    gff_path = discover_annotation_gff(
        annotation_directory
    )

    feature_counts: Counter[str] = Counter()
    feature_names: set[str] = set()

    with gff_path.open(
            "r",
            encoding="utf-8",
            errors="replace",
    ) as handle:
        for line_number, line in enumerate(
                handle,
                start=1,
        ):
            line = line.rstrip(
                "\n"
            )

            if not line:
                continue

            if line.startswith("#"):
                continue

            fields = line.split(
                "\t"
            )

            if len(fields) != 9:
                raise ValueError(
                    f"Invalid GFF row {line_number} in "
                    f"{gff_path}: expected 9 columns, "
                    f"found {len(fields)}."
                )

            feature_type = fields[2].strip()

            if feature_type:
                feature_counts[
                    feature_type
                ] += 1

            attributes = parse_gff_attributes(
                fields[8]
            )

            feature_name = (
                attributes.get("Name")
                or attributes.get("gene")
                or attributes.get("product")
                or attributes.get("ID")
            )

            if feature_name:
                feature_names.add(
                    feature_name
                )

    stats = AnnotationStats(
        sample_id=sample_id,
        gff_path=gff_path.resolve(),
        total_features=sum(
            feature_counts.values()
        ),
        feature_counts=dict(
            sorted(
                feature_counts.items()
            )
        ),
        feature_names=sorted(
            feature_names
        ),
    )

    if logger is not None:
        logger.info(
            f"Parsed {stats.total_features} annotation "
            f"features from {gff_path}."
        )

    return stats