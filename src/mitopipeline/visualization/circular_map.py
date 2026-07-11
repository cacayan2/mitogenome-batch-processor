"""circular_map.py

Publication-oriented circular mitochondrial genome map rendering.
"""

# Imports
from pathlib import Path
import logging
import math

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from mitopipeline.stats.visualization_stats import (
    CircularGenomeMapData,
    GenomeFeature,
    build_circular_map_data,
    validate_visualization_outputs,
)


FEATURE_COLORS = {
    "gene": "#4C78A8",
    "CDS": "#F58518",
    "tRNA": "#54A24B",
    "rRNA": "#B279A2",
}


def feature_midpoint_angle(
        feature: GenomeFeature,
        genome_length: int,
) -> float:
    """Return feature midpoint angle in radians."""
    midpoint = (
        feature.start
        + feature.end
    ) / 2.0

    return (
        midpoint
        / genome_length
        * 2.0
        * math.pi
    )


def coordinate_to_angle(
        coordinate: int,
        genome_length: int,
) -> float:
    """Convert a one-based genome coordinate to Matplotlib angle."""
    return (
        coordinate
        - 1
    ) / genome_length * 360.0


def feature_arc_angles(
        feature: GenomeFeature,
        genome_length: int,
) -> tuple[float, float]:
    """Return arc start and end angles in degrees."""
    theta1 = coordinate_to_angle(
        feature.start,
        genome_length,
    )

    theta2 = coordinate_to_angle(
        feature.end,
        genome_length,
    )

    return theta1, theta2


def draw_feature_arc(
        axes,
        feature: GenomeFeature,
        genome_length: int,
        radius: float,
        width: float,
) -> None:
    """Draw one genome feature as a circular arc."""
    theta1, theta2 = feature_arc_angles(
        feature,
        genome_length,
    )

    if theta2 <= theta1:
        theta2 = theta1 + 0.5

    color = FEATURE_COLORS.get(
        feature.feature_type,
        "#777777",
    )

    wedge = patches.Wedge(
        center=(
            0,
            0,
        ),
        r=radius,
        theta1=theta1,
        theta2=theta2,
        width=width,
        facecolor=color,
        edgecolor="white",
        linewidth=0.6,
        alpha=0.95,
    )

    axes.add_patch(
        wedge
    )


def draw_feature_label(
        axes,
        feature: GenomeFeature,
        genome_length: int,
        radius: float,
) -> None:
    """Draw a label for one genome feature."""
    angle = feature_midpoint_angle(
        feature,
        genome_length,
    )

    x = math.cos(
        angle
    ) * radius

    y = math.sin(
        angle
    ) * radius

    angle_degrees = math.degrees(
        angle
    )

    rotation = angle_degrees

    horizontal_alignment = "left"

    if 90 < angle_degrees < 270:
        rotation = angle_degrees + 180
        horizontal_alignment = "right"

    axes.text(
        x,
        y,
        feature.label,
        fontsize=7,
        rotation=rotation,
        rotation_mode="anchor",
        ha=horizontal_alignment,
        va="center",
    )


def draw_tick_labels(
        axes,
        genome_length: int,
        radius: float,
) -> None:
    """Draw coordinate tick labels around the genome."""
    tick_count = 8

    for index in range(
            tick_count
    ):
        coordinate = int(
            genome_length
            * index
            / tick_count
        )

        label = (
            "0 bp"
            if coordinate == 0
            else f"{coordinate / 1000:.1f} kb"
        )

        angle = (
            index
            / tick_count
            * 2.0
            * math.pi
        )

        inner_x = math.cos(
            angle
        ) * (
            radius
            - 0.02
        )

        inner_y = math.sin(
            angle
        ) * (
            radius
            - 0.02
        )

        outer_x = math.cos(
            angle
        ) * (
            radius
            + 0.04
        )

        outer_y = math.sin(
            angle
        ) * (
            radius
            + 0.04
        )

        text_x = math.cos(
            angle
        ) * (
            radius
            + 0.13
        )

        text_y = math.sin(
            angle
        ) * (
            radius
            + 0.13
        )

        axes.plot(
            [
                inner_x,
                outer_x,
            ],
            [
                inner_y,
                outer_y,
            ],
            linewidth=0.6,
            color="black",
        )

        axes.text(
            text_x,
            text_y,
            label,
            fontsize=6,
            ha="center",
            va="center",
        )


def draw_legend(
        axes,
) -> None:
    """Draw feature-type legend."""
    handles = [
        patches.Patch(
            color=color,
            label=feature_type,
        )
        for feature_type, color in FEATURE_COLORS.items()
    ]

    axes.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(
            0.5,
            -0.08,
        ),
        ncol=4,
        frameon=False,
        fontsize=8,
    )


def render_circular_map_data(
        map_data: CircularGenomeMapData,
        output_png: str | Path,
        output_svg: str | Path,
        output_pdf: str | Path,
        dpi: int = 600,
        logger: logging.Logger | None = None,
) -> None:
    """Render circular mitochondrial genome map outputs."""
    if dpi <= 0:
        raise ValueError(
            "Visualization DPI must be greater than zero."
        )

    output_png = Path(
        output_png
    )
    output_svg = Path(
        output_svg
    )
    output_pdf = Path(
        output_pdf
    )

    output_paths = [
        output_png,
        output_svg,
        output_pdf,
    ]

    for output_path in output_paths:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    figure, axes = plt.subplots(
        figsize=(
            9,
            9,
        )
    )

    try:
        axes.set_aspect(
            "equal"
        )
        axes.axis(
            "off"
        )

        outer_radius = 1.0
        forward_radius = 1.0
        reverse_radius = 0.86
        feature_width = 0.10

        backbone = patches.Circle(
            (
                0,
                0,
            ),
            radius=outer_radius,
            fill=False,
            linewidth=1.0,
            color="black",
        )

        axes.add_patch(
            backbone
        )

        # Draw every normalized segment. Origin-crossing features have two
        # segments and therefore produce two arcs.
        for feature in map_data.features:
            radius = (
                forward_radius
                if feature.strand != "-"
                else reverse_radius
            )

            draw_feature_arc(
                axes=axes,
                feature=feature,
                genome_length=map_data.genome_length,
                radius=radius,
                width=feature_width,
            )

        # Draw only one label for each logical feature. Segment suffixes were
        # added by build_circular_map_data() when a feature crossed the origin.
        labeled_feature_ids: set[str] = set()

        for feature in map_data.features:
            logical_feature_id = feature.feature_id.split(
                ":origin-",
                maxsplit=1,
            )[0]

            if logical_feature_id in labeled_feature_ids:
                continue

            label_radius = (
                1.18
                if feature.strand != "-"
                else 0.72
            )

            draw_feature_label(
                axes=axes,
                feature=feature,
                genome_length=map_data.genome_length,
                radius=label_radius,
            )

            labeled_feature_ids.add(
                logical_feature_id
            )

        draw_tick_labels(
            axes=axes,
            genome_length=map_data.genome_length,
            radius=outer_radius,
        )

        draw_legend(
            axes
        )

        axes.text(
            0,
            0.08,
            map_data.sample_id,
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="center",
        )

        axes.text(
            0,
            -0.05,
            (
                f"{map_data.genome_length:,} bp"
                f"\nGC {map_data.gc_content_percent:.2f}%"
            ),
            fontsize=9,
            ha="center",
            va="center",
        )

        axes.set_xlim(
            -1.45,
            1.45,
        )
        axes.set_ylim(
            -1.45,
            1.45,
        )

        figure.tight_layout()

        figure.savefig(
            output_svg,
            bbox_inches="tight",
        )
        figure.savefig(
            output_pdf,
            bbox_inches="tight",
        )
        figure.savefig(
            output_png,
            dpi=dpi,
            bbox_inches="tight",
        )

    finally:
        plt.close(
            figure
        )

    validate_visualization_outputs(
        png_path=output_png,
        svg_path=output_svg,
        pdf_path=output_pdf,
        logger=logger,
    )

    if logger is not None:
        logger.info(
            "Rendered circular mitochondrial genome map for %s.",
            map_data.sample_id,
        )


def render_circular_genome_map(
        sample_id: str,
        gff_path: str | Path,
        fasta_path: str | Path,
        output_png: str | Path,
        output_svg: str | Path,
        output_pdf: str | Path,
        dpi: int = 600,
        logger: logging.Logger | None = None,
) -> CircularGenomeMapData:
    """Parse MITOS2 outputs and render a circular genome map."""
    map_data = build_circular_map_data(
        sample_id=sample_id,
        gff_path=gff_path,
        fasta_path=fasta_path,
        logger=logger,
    )

    render_circular_map_data(
        map_data=map_data,
        output_png=output_png,
        output_svg=output_svg,
        output_pdf=output_pdf,
        dpi=dpi,
        logger=logger,
    )

    return map_data
