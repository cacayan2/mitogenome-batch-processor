"""Alignment, IQ-TREE inference, and tree rendering rules."""

from pathlib import Path


def midpoint_root_argument() -> str:
    if config["tools"]["iqtree"].get(
        "midpoint_root_figure",
        True,
    ):
        return "--midpoint-root"
    return ""


rule align_phylogeny_dataset:
    input:
        fasta=str(
            JOB_DIR / "phylogeny" / "{sample}" / "dataset.fasta"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "dataset.done"
        )

    output:
        alignment=str(
            JOB_DIR / "phylogeny" / "{sample}" / "aligned.fasta"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "alignment.done"
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
                / "phylogeny"
                / "{sample}"
                / "alignment.log"
            ).resolve()
        )

    threads:
        config["tools"]["alignment"].get("threads", 4)

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_phylogeny_alignment \
            --sample-id {wildcards.sample} \
            --input-fasta {input.fasta:q} \
            --output-fasta {output.alignment:q} \
            --mafft-bin {params.executable:q} \
            --threads {threads} \
            --log-file {params.log_file:q}

        test -s {output.alignment:q}
        touch {output.done:q}
        """


rule infer_phylogeny:
    input:
        alignment=str(
            JOB_DIR / "phylogeny" / "{sample}" / "aligned.fasta"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "alignment.done"
        )

    output:
        newick=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.nwk"
        ),
        treefile=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.treefile"
        ),
        report=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.iqtree"
        ),
        iqtree_log=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.log"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "iqtree.done"
        )

    params:
        executable=config["tools"]["iqtree"].get(
            "executable",
            "iqtree3",
        ),
        output_prefix=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood"
        ),
        sequence_type=config["tools"]["iqtree"].get(
            "sequence_type",
            "DNA",
        ),
        model=config["tools"]["iqtree"].get("model", "MFP"),
        bootstrap=config["tools"]["iqtree"].get(
            "ultrafast_bootstrap",
            1000,
        ),
        sh_alrt=config["tools"]["iqtree"].get("sh_alrt", 1000),
        random_seed=config["tools"]["iqtree"].get(
            "random_seed",
            12345,
        ),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "iqtree_runner.log"
            ).resolve()
        )

    threads:
        config["tools"]["iqtree"].get("threads", 4)

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_iqtree \
            --sample-id {wildcards.sample} \
            --alignment {input.alignment:q} \
            --output-prefix {params.output_prefix:q} \
            --output-newick {output.newick:q} \
            --iqtree-bin {params.executable:q} \
            --threads {threads} \
            --sequence-type {params.sequence_type} \
            --model {params.model} \
            --ultrafast-bootstrap {params.bootstrap} \
            --sh-alrt {params.sh_alrt} \
            --random-seed {params.random_seed} \
            --log-file {params.log_file:q}

        test -s {output.newick:q}
        test -s {output.treefile:q}
        test -s {output.report:q}
        test -s {output.iqtree_log:q}
        touch {output.done:q}
        """


rule render_phylogenetic_tree:
    input:
        alignment=str(
            JOB_DIR / "phylogeny" / "{sample}" / "aligned.fasta"
        ),
        newick=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.nwk"
        ),
        report=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "maximum_likelihood.iqtree"
        ),
        tree_done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "iqtree.done"
        )

    output:
        svg=str(
            JOB_DIR / "phylogeny" / "{sample}" / "phylogeny.svg"
        ),
        pdf=str(
            JOB_DIR / "phylogeny" / "{sample}" / "phylogeny.pdf"
        ),
        png=str(
            JOB_DIR / "phylogeny" / "{sample}" / "phylogeny.png"
        ),
        summary=str(
            JOB_DIR / "phylogeny" / "{sample}" / "phylogeny.md"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "phylogeny.done"
        )

    params:
        dpi=config["tools"]["iqtree"].get("render_dpi", 600),
        bootstrap=config["tools"]["iqtree"].get(
            "ultrafast_bootstrap",
            1000,
        ),
        sh_alrt=config["tools"]["iqtree"].get("sh_alrt", 1000),
        midpoint_root_arg=midpoint_root_argument(),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "render.log"
            ).resolve()
        )

    conda:
        "../../envs/phylogeny.yaml"

    shell:
        """
        python -m mitopipeline.exec.render_phylogeny \
            --sample-id {wildcards.sample} \
            --alignment {input.alignment:q} \
            --input-newick {input.newick:q} \
            --iqtree-report {input.report:q} \
            --output-svg {output.svg:q} \
            --output-pdf {output.pdf:q} \
            --output-png {output.png:q} \
            --output-summary {output.summary:q} \
            --dpi {params.dpi} \
            --ultrafast-bootstrap {params.bootstrap} \
            --sh-alrt {params.sh_alrt} \
            {params.midpoint_root_arg} \
            --log-file {params.log_file:q}

        test -s {output.svg:q}
        test -s {output.pdf:q}
        test -s {output.png:q}
        test -s {output.summary:q}
        touch {output.done:q}
        """
