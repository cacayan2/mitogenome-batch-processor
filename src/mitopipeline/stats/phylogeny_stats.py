"""phylogeny_stats.py

Validation, parsing, and rendering functions for phylogenetic analyses.
"""

# Imports
import logging
import re
from pathlib import Path

import matplotlib.pyplot as plt
from Bio import Phylo, SeqIO
from Bio.Phylo.BaseTree import Tree
from Bio.SeqRecord import SeqRecord


def read_phylogeny_dataset(
        fasta_path: str | Path,
        expected_reference_count: int = 6,
        logger: logging.Logger | None = None,
) -> list[SeqRecord]:
    """Read and validate an unaligned phylogenetic FASTA dataset.

    Args:
        fasta_path (str | Path): Combined phylogenetic FASTA.
        expected_reference_count (int, optional): Expected number of
            BLAST references. Defaults to 6.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.

    Returns:
        list[SeqRecord]: Validated FASTA records.

    Raises:
        FileNotFoundError: If the input FASTA does not exist.
        ValueError: If sequence records are missing or invalid.
    """
    # Normalizing path.
    fasta_path = Path(fasta_path)

    # Verifying input path.
    if not fasta_path.exists():
        raise FileNotFoundError(
            f"Phylogeny FASTA not found: {fasta_path}."
        )

    if not fasta_path.is_file():
        raise ValueError(
            f"Phylogeny FASTA path is not a file: {fasta_path}."
        )

    # Reading sequences.
    records = list(
        SeqIO.parse(
            fasta_path,
            "fasta",
        )
    )

    expected_total = expected_reference_count + 1

    # Verifying sequence count.
    if len(records) != expected_total:
        raise ValueError(
            f"Expected {expected_total} phylogeny sequences "
            f"(one assembly and {expected_reference_count} references), "
            f"but found {len(records)}."
        )

    # Verifying assembly record.
    if not records[0].id.endswith("|assembled"):
        raise ValueError(
            "The assembled mitochondrial genome must be the first "
            "phylogeny FASTA record."
        )

    # Verifying identifiers.
    identifiers = [
        record.id
        for record in records
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            "Duplicate identifiers found in phylogeny FASTA."
        )

    # Verifying sequences.
    for record in records:
        if len(record.seq) == 0:
            raise ValueError(
                f"Phylogeny sequence is empty: {record.id}."
            )

    if logger is not None:
        logger.info(
            f"Validated {len(records)} phylogeny sequences from "
            f"{fasta_path}."
        )

    return records


def validate_alignment(
        alignment_path: str | Path,
        expected_sequence_count: int = 7,
        logger: logging.Logger | None = None,
) -> list[SeqRecord]:
    """Read and validate an aligned phylogenetic FASTA.

    Args:
        alignment_path (str | Path): Aligned FASTA path.
        expected_sequence_count (int, optional): Expected number of
            aligned sequences. Defaults to 7.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.

    Returns:
        list[SeqRecord]: Validated aligned records.

    Raises:
        FileNotFoundError: If the alignment does not exist.
        ValueError: If the alignment is invalid.
    """
    alignment_path = Path(alignment_path)

    if not alignment_path.exists():
        raise FileNotFoundError(
            f"Phylogeny alignment not found: {alignment_path}."
        )

    if not alignment_path.is_file():
        raise ValueError(
            f"Phylogeny alignment path is not a file: "
            f"{alignment_path}."
        )

    records = list(
        SeqIO.parse(
            alignment_path,
            "fasta",
        )
    )

    if len(records) != expected_sequence_count:
        raise ValueError(
            f"Expected {expected_sequence_count} aligned sequences, "
            f"but found {len(records)}."
        )

    identifiers = [
        record.id
        for record in records
    ]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError(
            "Duplicate sequence identifiers found in alignment."
        )

    sequence_lengths = {
        len(record.seq)
        for record in records
    }

    if len(sequence_lengths) != 1:
        raise ValueError(
            "Aligned sequences do not have equal lengths."
        )

    aligned_length = next(iter(sequence_lengths))

    if aligned_length == 0:
        raise ValueError(
            "Aligned sequences are empty."
        )

    if logger is not None:
        logger.info(
            f"Validated alignment containing {len(records)} sequences "
            f"and {aligned_length} alignment columns."
        )

    return records


def validate_newick_tree(
        tree_path: str | Path,
        expected_tip_count: int = 7,
        logger: logging.Logger | None = None,
) -> Tree:
    """Read and validate a Newick phylogenetic tree.

    Args:
        tree_path (str | Path): Newick tree path.
        expected_tip_count (int, optional): Expected tip count.
            Defaults to 7.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.

    Returns:
        Tree: Parsed Biopython tree.

    Raises:
        FileNotFoundError: If the tree file does not exist.
        ValueError: If the tree does not contain the expected taxa.
    """
    tree_path = Path(tree_path)

    if not tree_path.exists():
        raise FileNotFoundError(
            f"Newick tree not found: {tree_path}."
        )

    if not tree_path.is_file():
        raise ValueError(
            f"Newick tree path is not a file: {tree_path}."
        )

    tree = Phylo.read(
        tree_path,
        "newick",
    )

    terminals = tree.get_terminals()

    if len(terminals) != expected_tip_count:
        raise ValueError(
            f"Expected {expected_tip_count} tree tips, but found "
            f"{len(terminals)}."
        )

    terminal_names = [
        terminal.name
        for terminal in terminals
    ]

    if any(
        name is None or not name.strip()
        for name in terminal_names
    ):
        raise ValueError(
            "Every tree tip must have a non-empty name."
        )

    if len(terminal_names) != len(set(terminal_names)):
        raise ValueError(
            "Duplicate tree-tip names found."
        )

    if logger is not None:
        logger.info(
            f"Validated Newick tree containing "
            f"{len(terminals)} tips."
        )

    return tree


def format_tree_label(
    identifier: str,
) -> str:
    """Convert a pipeline FASTA identifier into a figure label."""
    parts = identifier.split("|")

    if len(parts) >= 2 and parts[-1] == "assembled":
        sample_name = parts[0].replace("_", " ")
        return f"{sample_name} (assembly)"

    # Species_name|accession|reference_01
    if len(parts) >= 3 and parts[-1].startswith("reference_"):
        species_name = parts[0].replace("_", " ")
        accession = parts[1]
        return f"{species_name} [{accession}]"

    # Legacy format: reference_01|accession|Species_name
    if len(parts) >= 3 and parts[0].startswith("reference_"):
        accession = parts[1]
        species_name = parts[2].replace("_", " ")
        return f"{species_name} [{accession}]"

    return identifier.replace("_", " ")


def prepare_tree_for_figure(
        tree: Tree,
        midpoint_root: bool = True,
) -> Tree:
    """Prepare a copy of a tree for publication rendering.

    Args:
        tree (Tree): Source phylogenetic tree.
        midpoint_root (bool, optional): Whether to midpoint-root the
            displayed tree. Defaults to True.

    Returns:
        Tree: Prepared tree copy.
    """
    # Copying tree so the original Newick topology is not modified.
    figure_tree = Tree.from_clade(
        tree.root,
        rooted=tree.rooted,
    )

    # Converting labels for display.
    for terminal in figure_tree.get_terminals():
        terminal.name = format_tree_label(
            terminal.name
        )

    # Midpoint rooting is used only for figure presentation.
    if midpoint_root and len(
        figure_tree.get_terminals()
    ) >= 2:
        figure_tree.root_at_midpoint()

    return figure_tree


def parse_iqtree_model(
        report_path: str | Path,
) -> str | None:
    """Extract the selected substitution model from an IQ-TREE report.

    Args:
        report_path (str | Path): IQ-TREE `.iqtree` report.

    Returns:
        str | None: Selected model, or None if it cannot be found.
    """
    report_path = Path(report_path)

    if not report_path.exists():
        return None

    report_text = report_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    patterns = [
        (
            r"Best-fit model according to BIC:\s*"
            r"([^\s]+)"
        ),
        (
            r"Best-fit model:\s*"
            r"([^\s]+)"
        ),
        (
            r"Model of substitution:\s*"
            r"([^\n]+)"
        ),
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            report_text,
            flags=re.IGNORECASE,
        )

        if match is not None:
            return match.group(1).strip()

    return None


def render_phylogenetic_tree(
        tree_path: str | Path,
        output_svg: str | Path,
        output_pdf: str | Path,
        output_png: str | Path,
        title: str,
        dpi: int = 600,
        midpoint_root: bool = True,
        logger: logging.Logger | None = None,
) -> None:
    """Render a Newick tree as SVG, PDF, and PNG.

    Args:
        tree_path (str | Path): Newick input tree.
        output_svg (str | Path): SVG output path.
        output_pdf (str | Path): PDF output path.
        output_png (str | Path): PNG output path.
        title (str): Figure title.
        dpi (int, optional): PNG resolution. Defaults to 600.
        midpoint_root (bool, optional): Midpoint-root display tree.
            Defaults to True.
        logger (logging.Logger | None, optional): Logger to use.
            Defaults to None.
    """
    if dpi <= 0:
        raise ValueError(
            "Tree figure DPI must be greater than zero."
        )

    source_tree = validate_newick_tree(
        tree_path=tree_path,
        expected_tip_count=7,
        logger=logger,
    )

    figure_tree = prepare_tree_for_figure(
        tree=source_tree,
        midpoint_root=midpoint_root,
    )

    output_svg = Path(output_svg)
    output_pdf = Path(output_pdf)
    output_png = Path(output_png)

    for output_path in [
        output_svg,
        output_pdf,
        output_png,
    ]:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    terminal_count = len(
        figure_tree.get_terminals()
    )

    figure_height = max(
        5.0,
        terminal_count * 0.75,
    )

    figure = plt.figure(
        figsize=(12, figure_height),
    )

    axes = figure.add_subplot(
        1,
        1,
        1,
    )

    Phylo.draw(
        figure_tree,
        axes=axes,
        do_show=False,
        show_confidence=True,
    )

    axes.set_title(title)
    axes.set_xlabel(
        "Substitutions per site"
    )
    axes.set_ylabel("")

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

    plt.close(figure)

    if logger is not None:
        logger.info(
            f"Rendered tree figure to {output_svg}, "
            f"{output_pdf}, and {output_png}."
        )


def write_phylogeny_summary(
        sample_id: str,
        alignment_path: str | Path,
        tree_path: str | Path,
        report_path: str | Path,
        output_path: str | Path,
        ultrafast_bootstrap: int,
        sh_alrt: int,
        midpoint_root_figure: bool,
        logger: logging.Logger | None = None,
) -> None:
    """Write a per-sample phylogenetic-method summary.

    Args:
        sample_id (str): Pipeline sample identifier.
        alignment_path (str | Path): Alignment path.
        tree_path (str | Path): Newick tree path.
        report_path (str | Path): IQ-TREE report path.
        output_path (str | Path): Markdown output path.
        ultrafast_bootstrap (int): UFBoot replicate count.
        sh_alrt (int): SH-aLRT replicate count.
        midpoint_root_figure (bool): Whether figure was midpoint rooted.
        logger (logging.Logger | None): Optional logger.
    """
    model = parse_iqtree_model(
        report_path
    )

    model_text = (
        model
        if model is not None
        else "See the accompanying IQ-TREE report"
    )

    rooting_text = (
        "The publication figure was midpoint rooted for display; "
        "the Newick file preserves the inferred IQ-TREE topology."
        if midpoint_root_figure
        else
        "The publication figure preserves the unrooted IQ-TREE tree."
    )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_text = f"""# Phylogenetic validation: {sample_id}

## Dataset

The analysis contains the assembled mitochondrial genome and the six
highest-ranked unique BLAST reference sequences.

## Method

Sequences were aligned with MAFFT. Maximum-likelihood phylogenetic
inference and automatic model selection were performed with IQ-TREE.

- Selected substitution model: `{model_text}`
- Ultrafast bootstrap replicates: `{ultrafast_bootstrap}`
- SH-aLRT replicates: `{sh_alrt}`
- Alignment: `{alignment_path}`
- Newick tree: `{tree_path}`
- IQ-TREE report: `{report_path}`

{rooting_text}

## Figure files

The SVG and PDF outputs are vector graphics suitable for editing and
journal submission. The PNG output is rendered at publication resolution.
"""

    output_path.write_text(
        output_text,
        encoding="utf-8",
    )

    if logger is not None:
        logger.info(
            f"Wrote phylogeny summary to {output_path}."
        )