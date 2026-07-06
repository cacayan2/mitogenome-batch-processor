"""run_iqtree.py

Execution layer for IQ-TREE maximum-likelihood phylogenetic inference.
"""

# Imports
import argparse
import shutil
import subprocess
from pathlib import Path

from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.stats.phylogeny_stats import (
    validate_alignment,
    validate_newick_tree,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Infer a maximum-likelihood mitochondrial phylogeny "
            "with IQ-TREE."
        )
    )

    parser.add_argument(
        "--sample-id",
        required=True,
    )

    parser.add_argument(
        "--alignment",
        required=True,
    )

    parser.add_argument(
        "--output-prefix",
        required=True,
    )

    parser.add_argument(
        "--output-newick",
        required=True,
    )

    parser.add_argument(
        "--iqtree-bin",
        default="iqtree3",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--sequence-type",
        default="DNA",
    )

    parser.add_argument(
        "--model",
        default="MFP",
    )

    parser.add_argument(
        "--ultrafast-bootstrap",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--sh-alrt",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=12345,
    )

    parser.add_argument(
        "--log-file",
        required=True,
    )

    return parser.parse_args()


def resolve_iqtree_executable(
        preferred_executable: str,
) -> str:
    """Resolve an installed IQ-TREE executable.

    Args:
        preferred_executable (str): Preferred executable name.

    Returns:
        str: Resolved executable path.

    Raises:
        FileNotFoundError: If IQ-TREE is not available.
    """
    candidates = [
        preferred_executable,
        "iqtree3",
        "iqtree2",
        "iqtree",
    ]

    checked = set()

    for candidate in candidates:
        if candidate in checked:
            continue

        checked.add(candidate)

        executable_path = shutil.which(
            candidate
        )

        if executable_path is not None:
            return executable_path

    raise FileNotFoundError(
        "Could not locate an IQ-TREE executable. Checked: "
        + ", ".join(checked)
    )


def run_iqtree(
        alignment_path: str | Path,
        output_prefix: str | Path,
        output_newick: str | Path,
        iqtree_bin: str,
        threads: int,
        sequence_type: str,
        model: str,
        ultrafast_bootstrap: int,
        sh_alrt: int,
        random_seed: int,
        logger,
) -> None:
    """Run IQ-TREE model selection and maximum-likelihood inference.

    Args:
        alignment_path (str | Path): Aligned FASTA.
        output_prefix (str | Path): IQ-TREE output prefix.
        output_newick (str | Path): Normalized Newick output.
        iqtree_bin (str): Preferred IQ-TREE executable.
        threads (int): Thread count.
        sequence_type (str): IQ-TREE sequence type.
        model (str): Model-selection setting.
        ultrafast_bootstrap (int): UFBoot replicate count.
        sh_alrt (int): SH-aLRT replicate count.
        random_seed (int): Reproducible random seed.
        logger: Execution logger.
    """
    if threads <= 0:
        raise ValueError(
            "IQ-TREE threads must be greater than zero."
        )

    if ultrafast_bootstrap < 1000:
        raise ValueError(
            "IQ-TREE ultrafast-bootstrap replicates must be "
            "at least 1000."
        )

    if sh_alrt < 1000:
        raise ValueError(
            "IQ-TREE SH-aLRT replicates must be at least 1000."
        )

    alignment_path = Path(alignment_path)
    output_prefix = Path(output_prefix)
    output_newick = Path(output_newick)

    validate_alignment(
        alignment_path=alignment_path,
        expected_sequence_count=7,
        logger=logger,
    )

    output_prefix.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_newick.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    executable = resolve_iqtree_executable(
        iqtree_bin
    )

    command = [
        executable,
        "-s",
        str(alignment_path),
        "-st",
        sequence_type,
        "-m",
        model,
        "-B",
        str(ultrafast_bootstrap),
        "--alrt",
        str(sh_alrt),
        "-T",
        str(threads),
        "--seed",
        str(random_seed),
        "--prefix",
        str(output_prefix),
    ]

    logger.info(
        "Running IQ-TREE command: "
        + " ".join(command)
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        logger.info(
            result.stdout.strip()
        )

    if result.stderr:
        logger.info(
            result.stderr.strip()
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"IQ-TREE failed with exit code {result.returncode}."
        )

    generated_tree = Path(
        f"{output_prefix}.treefile"
    )

    if not generated_tree.exists():
        raise FileNotFoundError(
            "IQ-TREE completed without producing its expected "
            f"tree file: {generated_tree}."
        )

    shutil.copyfile(
        generated_tree,
        output_newick,
    )

    validate_newick_tree(
        tree_path=output_newick,
        expected_tip_count=7,
        logger=logger,
    )


def main() -> int:
    """Run IQ-TREE phylogenetic inference.

    Returns:
        int: Exit code.
    """
    logger = None

    try:
        args = parse_args()

        logger = make_logger(
            name="iqtree",
            log_file_path=args.log_file,
        )

        logger.info(
            f"Starting IQ-TREE analysis for "
            f"sample {args.sample_id}."
        )

        run_iqtree(
            alignment_path=args.alignment,
            output_prefix=args.output_prefix,
            output_newick=args.output_newick,
            iqtree_bin=args.iqtree_bin,
            threads=args.threads,
            sequence_type=args.sequence_type,
            model=args.model,
            ultrafast_bootstrap=args.ultrafast_bootstrap,
            sh_alrt=args.sh_alrt,
            random_seed=args.random_seed,
            logger=logger,
        )

        logger.info(
            f"Completed IQ-TREE analysis for "
            f"sample {args.sample_id}."
        )

        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"IQ-TREE analysis failed: {error}"
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())