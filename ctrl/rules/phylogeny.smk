"""phylogeny.smk

Align mitochondrial genomes, infer an IQ-TREE phylogeny, and produce
publication-ready tree figures.
"""

# Imports
from pathlib import Path


def midpoint_root_argument() -> str:
    """Return midpoint-root CLI argument when enabled."""
    if config["tools"]["iqtree"].get(
        "midpoint_root_figure",
        True,
    ):
        return "--midpoint-root"

    return ""


rule align_phylogeny_dataset:
    """Align the assembly and six selected BLAST references."""

    input:
        fasta=str(
            JOB_DIR
            / "phylogeny"
            / "datasets"
            / "{sample}.phylogeny.fasta"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "datasets"
            / "{sample}.phylogeny.done"
        )

    output:
        alignment=str(
            JOB_DIR
            / "phylogeny"
            / "alignment"
            / "{sample}.aligned.fasta"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "alignment"
            / "{sample}.alignment.done"
        )

    params:
        executable=config["tools"]["alignment"].get(
            "executable",
            "mafft",
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "phylogeny_alignment"
                / "{sample}.log"
            ).resolve()
        )

    threads:
        config["tools"]["alignment"].get(
            "threads",
            4,
        )

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.run_phylogeny_alignment \
            --sample-id {wildcards.sample} \
            --input-fasta {input.fasta} \
            --output-fasta {output.alignment} \
            --mafft-bin {params.executable} \
            --threads {threads} \
            --log-file {params.log_file}

        touch {output.done}
        """


rule infer_phylogeny:
    """Infer a maximum-likelihood phylogeny with IQ-TREE."""

    input:
        alignment=str(
            JOB_DIR
            / "phylogeny"
            / "alignment"
            / "{sample}.aligned.fasta"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "alignment"
            / "{sample}.alignment.done"
        )

    output:
        newick=str(
            JOB_DIR
            / "phylogeny"
            / "trees"
            / "{sample}.maximum_likelihood.nwk"
        ),
        treefile=str(
            JOB_DIR
            / "phylogeny"
            / "iqtree"
            / "{sample}.maximum_likelihood.treefile"
        ),
        report=str(
            JOB_DIR
            / "phylogeny"
            / "iqtree"
            / "{sample}.maximum_likelihood.iqtree"
        ),
        iqtree_log=str(
            JOB_DIR
            / "phylogeny"
            / "iqtree"
            / "{sample}.maximum_likelihood.log"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "trees"
            / "{sample}.iqtree.done"
        )

    params:
        executable=config["tools"]["iqtree"].get(
            "executable",
            "iqtree3",
        ),
        output_prefix=str(
            JOB_DIR
            / "phylogeny"
            / "iqtree"
            / "{sample}.maximum_likelihood"
        ),
        sequence_type=config["tools"]["iqtree"].get(
            "sequence_type",
            "DNA",
        ),
        model=config["tools"]["iqtree"].get(
            "model",
            "MFP",
        ),
        bootstrap=config["tools"]["iqtree"].get(
            "ultrafast_bootstrap",
            1000,
        ),
        sh_alrt=config["tools"]["iqtree"].get(
            "sh_alrt",
            1000,
        ),
        random_seed=config["tools"]["iqtree"].get(
            "random_seed",
            12345,
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "iqtree"
                / "{sample}.log"
            ).resolve()
        )

    threads:
        config["tools"]["iqtree"].get(
            "threads",
            4,
        )

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.run_iqtree \
            --sample-id {wildcards.sample} \
            --alignment {input.alignment} \
            --output-prefix {params.output_prefix} \
            --output-newick {output.newick} \
            --iqtree-bin {params.executable} \
            --threads {threads} \
            --sequence-type {params.sequence_type} \
            --model {params.model} \
            --ultrafast-bootstrap {params.bootstrap} \
            --sh-alrt {params.sh_alrt} \
            --random-seed {params.random_seed} \
            --log-file {params.log_file}

        touch {output.done}
        """


rule render_phylogenetic_tree:
    """Render publication-ready phylogeny figures and documentation."""

    input:
        alignment=str(
            JOB_DIR
            / "phylogeny"
            / "alignment"
            / "{sample}.aligned.fasta"
        ),
        newick=str(
            JOB_DIR
            / "phylogeny"
            / "trees"
            / "{sample}.maximum_likelihood.nwk"
        ),
        report=str(
            JOB_DIR
            / "phylogeny"
            / "iqtree"
            / "{sample}.maximum_likelihood.iqtree"
        ),
        tree_done=str(
            JOB_DIR
            / "phylogeny"
            / "trees"
            / "{sample}.iqtree.done"
        )

    output:
        svg=str(
            JOB_DIR
            / "phylogeny"
            / "figures"
            / "{sample}.maximum_likelihood.svg"
        ),
        pdf=str(
            JOB_DIR
            / "phylogeny"
            / "figures"
            / "{sample}.maximum_likelihood.pdf"
        ),
        png=str(
            JOB_DIR
            / "phylogeny"
            / "figures"
            / "{sample}.maximum_likelihood.png"
        ),
        summary=str(
            JOB_DIR
            / "phylogeny"
            / "figures"
            / "{sample}.phylogeny.md"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "figures"
            / "{sample}.phylogeny.done"
        )

    params:
        dpi=config["tools"]["iqtree"].get(
            "render_dpi",
            600,
        ),
        bootstrap=config["tools"]["iqtree"].get(
            "ultrafast_bootstrap",
            1000,
        ),
        sh_alrt=config["tools"]["iqtree"].get(
            "sh_alrt",
            1000,
        ),
        midpoint_root_arg=midpoint_root_argument(),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "logs"
                / "phylogeny_render"
                / "{sample}.log"
            ).resolve()
        )

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.render_phylogeny \
            --sample-id {wildcards.sample} \
            --alignment {input.alignment} \
            --input-newick {input.newick} \
            --iqtree-report {input.report} \
            --output-svg {output.svg} \
            --output-pdf {output.pdf} \
            --output-png {output.png} \
            --output-summary {output.summary} \
            --dpi {params.dpi} \
            --ultrafast-bootstrap {params.bootstrap} \
            --sh-alrt {params.sh_alrt} \
            {params.midpoint_root_arg} \
            --log-file {params.log_file}

        touch {output.done}
        """