"""visualization_stats.py

Parsing and validation utilities for circular mitochondrial genome maps.
"""

# Imports
from dataclasses import asdict, dataclass
from pathlib import Path
import logging
import re

from Bio import SeqIO


FEATURE_TYPES_TO_DRAW = {
    "gene",
    "CDS",
    "tRNA",
    "rRNA",
}


@dataclass(frozen=True)
class GenomeFeature:
    """Feature used in a circular mitochondrial genome map."""

    feature_id: str
    feature_type: str
    start: int
    end: int
    strand: str
    label: str

    @property
    def length(self) -> int:
        """Return feature length in base pairs."""
        return abs(
            self.end
            - self.start
        ) + 1

    def to_dict(self) -> dict:
        """Convert the feature to a dictionary."""
        return asdict(
            self
        )


@dataclass(frozen=True)
class CircularGenomeMapData:
    """Parsed data required to draw a circular genome map."""

    sample_id: str
    genome_length: int
    sequence_id: str
    gc_content_percent: float
    features: list[GenomeFeature]
    gff_path: Path
    fasta_path: Path

    def to_dict(self) -> dict:
        """Convert map data to a dictionary."""
        data = asdict(
            self
        )

        data["gff_path"] = str(
            self.gff_path
        )

        data["fasta_path"] = str(
            self.fasta_path
        )

        data["features"] = [
            feature.to_dict()
            for feature in self.features
        ]

        return data


def parse_gff_attributes(
        attributes_text: str,
) -> dict[str, str]:
    """Parse GFF3 attributes into a dictionary."""
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


def normalize_feature_label(
        value: str,
) -> str:
    """Normalize a feature label for figure display."""
    value = value.strip()

    value = re.sub(
        r"^gene-",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = value.replace(
        "_",
        " ",
    )

    return value


def choose_feature_label(
        feature_type: str,
        attributes: dict[str, str],
        fallback_id: str,
) -> str:
    """Choose the best label from GFF attributes."""
    for key in [
        "Name",
        "gene",
        "product",
        "ID",
    ]:
        value = attributes.get(
            key
        )

        if value:
            return normalize_feature_label(
                value
            )

    return normalize_feature_label(
        fallback_id
    )


def parse_visualization_gff(
        gff_path: str | Path,
        logger: logging.Logger | None = None,
) -> list[GenomeFeature]:
    """Parse drawable features from a MITOS2 GFF/GFF3 file.

    Args:
        gff_path (str | Path): MITOS2 result GFF path.
        logger (logging.Logger | None, optional): Logger.

    Returns:
        list[GenomeFeature]: Parsed features.

    Raises:
        FileNotFoundError: If the GFF file is missing.
        ValueError: If the GFF file is malformed.
    """
    gff_path = Path(
        gff_path
    ).expanduser().resolve()

    if not gff_path.exists():
        raise FileNotFoundError(
            f"Visualization GFF not found: {gff_path}."
        )

    if not gff_path.is_file():
        raise ValueError(
            f"Visualization GFF path is not a file: "
            f"{gff_path}."
        )

    features: list[GenomeFeature] = []

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

            if not line or line.startswith(
                "#"
            ):
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

            feature_type = fields[
                2
            ].strip()

            if feature_type not in FEATURE_TYPES_TO_DRAW:
                continue

            try:
                start = int(
                    fields[3]
                )

                end = int(
                    fields[4]
                )

            except ValueError as error:
                raise ValueError(
                    f"Invalid feature coordinates on row "
                    f"{line_number} in {gff_path}."
                ) from error

            if start <= 0 or end <= 0:
                raise ValueError(
                    f"GFF coordinates must be positive on row "
                    f"{line_number} in {gff_path}."
                )

            attributes = parse_gff_attributes(
                fields[8]
            )

            feature_id = (
                attributes.get(
                    "ID"
                )
                or attributes.get(
                    "Name"
                )
                or f"{feature_type}_{line_number}"
            )

            label = choose_feature_label(
                feature_type=feature_type,
                attributes=attributes,
                fallback_id=feature_id,
            )

            strand = fields[6].strip()

            if strand not in {
                "+",
                "-",
                ".",
                "?",
            }:
                strand = "."

            features.append(
                GenomeFeature(
                    feature_id=feature_id,
                    feature_type=feature_type,
                    start=min(
                        start,
                        end,
                    ),
                    end=max(
                        start,
                        end,
                    ),
                    strand=strand,
                    label=label,
                )
            )

    if not features:
        raise ValueError(
            f"No drawable mitochondrial features were found in "
            f"{gff_path}."
        )

    features.sort(
        key=lambda feature: (
            feature.start,
            feature.end,
            feature.feature_type,
            feature.label,
        )
    )

    if logger is not None:
        logger.info(
            f"Parsed {len(features)} drawable features from "
            f"{gff_path}."
        )

    return features


def read_visualization_fasta(
        fasta_path: str | Path,
) -> tuple[str, int, float]:
    """Read the genome FASTA used to determine map length and GC content.

    Args:
        fasta_path (str | Path): MITOS2 result FASTA path.

    Returns:
        tuple[str, int, float]: Sequence ID, sequence length, GC percent.

    Raises:
        FileNotFoundError: If the FASTA file is missing.
        ValueError: If the FASTA file is invalid.
    """
    fasta_path = Path(
        fasta_path
    ).expanduser().resolve()

    if not fasta_path.exists():
        raise FileNotFoundError(
            f"Visualization FASTA not found: {fasta_path}."
        )

    if not fasta_path.is_file():
        raise ValueError(
            f"Visualization FASTA path is not a file: "
            f"{fasta_path}."
        )

    records = list(
        SeqIO.parse(
            fasta_path,
            "fasta",
        )
    )

    if not records:
        raise ValueError(
            f"No sequences found in visualization FASTA: "
            f"{fasta_path}."
        )

    if len(records) > 1:
        # MITOS2 usually emits one finalized sequence for a sample.
        # For visualization, use the first sequence deterministically.
        records = [
            records[0]
        ]

    record = records[0]
    sequence = str(
        record.seq
    ).upper()

    if not sequence:
        raise ValueError(
            f"Empty sequence found in visualization FASTA: "
            f"{fasta_path}."
        )

    valid_bases = [
        base
        for base in sequence
        if base in {
            "A",
            "C",
            "G",
            "T",
        }
    ]

    if valid_bases:
        gc_count = sum(
            base in {
                "G",
                "C",
            }
            for base in valid_bases
        )

        gc_content_percent = (
            gc_count
            / len(
                valid_bases
            )
            * 100.0
        )

    else:
        gc_content_percent = 0.0

    return (
        record.id,
        len(
            sequence
        ),
        gc_content_percent,
    )


def build_circular_map_data(
        sample_id: str,
        gff_path: str | Path,
        fasta_path: str | Path,
        logger: logging.Logger | None = None,
) -> CircularGenomeMapData:
    """Build parsed circular genome map data from MITOS2 outputs."""
    sequence_id, genome_length, gc_content_percent = read_visualization_fasta(
        fasta_path
    )

    features = parse_visualization_gff(
        gff_path=gff_path,
        logger=logger,
    )

    out_of_bounds = [
        feature
        for feature in features
        if feature.end > genome_length
    ]

    if out_of_bounds:
        names = ", ".join(
            feature.label
            for feature in out_of_bounds[:5]
        )

        raise ValueError(
            "One or more GFF features exceed the FASTA genome "
            f"length ({genome_length} bp): {names}."
        )

    return CircularGenomeMapData(
        sample_id=sample_id,
        genome_length=genome_length,
        sequence_id=sequence_id,
        gc_content_percent=gc_content_percent,
        features=features,
        gff_path=Path(
            gff_path
        ).expanduser().resolve(),
        fasta_path=Path(
            fasta_path
        ).expanduser().resolve(),
    )


def validate_visualization_outputs(
        png_path: str | Path,
        svg_path: str | Path,
        pdf_path: str | Path,
        logger: logging.Logger | None = None,
) -> None:
    """Validate circular genome map output files."""
    for output_path in [
        Path(
            png_path
        ),
        Path(
            svg_path
        ),
        Path(
            pdf_path
        ),
    ]:
        if not output_path.exists():
            raise FileNotFoundError(
                f"Visualization output was not created: "
                f"{output_path}."
            )

        if not output_path.is_file():
            raise ValueError(
                f"Visualization output is not a file: "
                f"{output_path}."
            )

        if output_path.stat().st_size == 0:
            raise ValueError(
                f"Visualization output is empty: "
                f"{output_path}."
            )

    if logger is not None:
        logger.info(
            "Validated circular genome map outputs."
        )
